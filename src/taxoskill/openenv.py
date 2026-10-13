"""Environment-agnostic OpenEnv discovery, transport, and agent bridge."""

from __future__ import annotations

import asyncio
from contextlib import suppress
import json
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from huggingface_hub import get_token
from jsonschema.validators import validator_for
from openenv.core import EnvClient
from openenv.core.client_types import StepResult as WireStepResult
import requests
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import SecurityError

from taxoskill.config import EnvCfg
from taxoskill.environment import AgentContext, Env, Observation, StepResult, ToolSpec


def _discovery_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Retry read-only discovery, never reset/step or other environment mutations."""
    method = method.upper()
    path = urlsplit(url).path
    if method != "GET" and not (method == "POST" and path.endswith("/tasks")):
        raise ValueError("discovery retries are limited to read-only endpoints")
    kwargs.setdefault("timeout", 60)
    transient_statuses = {429, 500, 502, 503, 504}
    for attempt in range(6):
        try:
            response = requests.request(method, url, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 5:
                raise
        else:
            if response.status_code not in transient_statuses or attempt == 5:
                response.raise_for_status()
                return response
            response.close()
        time.sleep(2 ** attempt)
    raise RuntimeError("discovery retry loop exhausted")


class _AuthenticatedConnect(ws_connect):
    def process_redirect(self, exc: Exception) -> Exception | str:
        result = super().process_redirect(exc)
        if isinstance(result, str):
            return SecurityError("Authenticated WebSocket redirects are disabled")
        return result


def _authenticated_ws_connect(uri: str, *, bearer_token: str, **kwargs: Any):
    return _AuthenticatedConnect(
        uri,
        additional_headers={"Authorization": f"Bearer {bearer_token}"},
        **kwargs,
    )


class GenericOpenEnvClient(EnvClient[dict[str, Any], dict[str, Any], dict[str, Any]]):
    """Raw JSON OpenEnv client requiring no environment Python package."""

    def __init__(self, *args: Any, bearer_token: str, **kwargs: Any) -> None:
        self._bearer_token = bearer_token
        super().__init__(*args, **kwargs)

    async def _connect_async(self) -> GenericOpenEnvClient:
        if self._ws is not None:
            if self._ws_loop is asyncio.get_running_loop():
                return self
            self._ws = None
            self._ws_loop = None
        self._start_provider_if_needed()
        assert self._ws_url is not None
        try:
            self._ws = await _authenticated_ws_connect(
                self._ws_url,
                bearer_token=self._bearer_token,
                open_timeout=self._connect_timeout,
                max_size=self._max_message_size,
                ping_interval=self._websocket_ping_interval_s,
                ping_timeout=self._websocket_ping_timeout_s,
            )
            self._ws_loop = asyncio.get_running_loop()
        except Exception as error:
            await self.close()
            raise ConnectionError(f"Failed to connect to {self._ws_url}: {error}") from error
        return self

    async def _send_and_receive(self, message: dict[str, Any]) -> dict[str, Any]:
        try:
            return await asyncio.wait_for(
                super()._send_and_receive(message),
                timeout=self._message_timeout,
            )
        except BaseException:
            websocket = self._ws
            self._ws = None
            self._ws_loop = None
            if websocket is not None:
                with suppress(BaseException):
                    await asyncio.wait_for(websocket.close(), timeout=5.0)
            raise

    async def _disconnect_async(self) -> None:
        websocket = self._ws
        websocket_loop = self._ws_loop
        self._ws = None
        self._ws_loop = None
        if websocket is None or websocket_loop is not asyncio.get_running_loop():
            return
        cleanup_timeout = min(float(self._message_timeout), 5.0)
        with suppress(BaseException):
            await asyncio.wait_for(
                websocket.send(json.dumps({"type": "close"})),
                timeout=cleanup_timeout,
            )
        with suppress(BaseException):
            await asyncio.wait_for(websocket.close(), timeout=cleanup_timeout)

    def _step_payload(self, action: dict[str, Any]) -> dict[str, Any]:
        return action

    def _parse_result(self, payload: dict[str, Any]) -> WireStepResult[dict[str, Any]]:
        # OpenEnv wire format: observation, reward, done always; metadata optional.
        reward = payload["reward"]
        return WireStepResult(
            observation=dict(payload["observation"]),
            reward=None if reward is None else float(reward),
            done=bool(payload["done"]),
            metadata=payload["metadata"] if "metadata" in payload else None,
        )

    def _parse_state(self, payload: dict[str, Any]) -> dict[str, Any]:
        return dict(payload)


def _http_base(base_url: str) -> str:
    parts = urlsplit(base_url)
    scheme = {"ws": "http", "wss": "https"}.get(parts.scheme.lower(), parts.scheme)
    return urlunsplit((scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


class OpenEnvEnvironment(Env):
    """Generic agent bridge driven entirely by endpoint discovery."""

    def __init__(
        self,
        client: Any,
        *,
        client_factory: Any,
        base_url: str,
        headers: dict[str, str],
        metadata: dict[str, Any],
        env_name: str,
        tools: list[ToolSpec] | tuple[ToolSpec, ...] = (),
        task_records: dict[str, list[dict[str, Any]]] | None = None,
        reset_options: dict[str, Any] | None = None,
    ) -> None:
        self._client = client
        # Forwarded verbatim on every reset (per-run protocol switches); the server rejects
        # unknown or missing required keywords itself.
        self._reset_options = {} if reset_options is None else dict(reset_options)
        self._client_factory = client_factory
        self._base_url = _http_base(base_url)
        self._headers = headers
        self._context = AgentContext(
            metadata=metadata,
            tools=tuple(tools),
        )
        self._env_name = env_name
        # Task records already fetched by a probe. A worker environment resets tasks from a
        # split it never listed itself, so the records must be handed over explicitly.
        self._task_records: dict[str, list[dict[str, Any]]] = (
            {} if task_records is None else {k: list(v) for k, v in task_records.items()}
        )
        self._active_task: dict[str, Any] | None = None
        self._observation: dict[str, Any] | None = None
        self._reward = 0.0
        self._closed = False

    def agent_context(self) -> AgentContext:
        return self._context

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = _discovery_request(
            method,
            self._base_url + path,
            headers=self._headers,
            timeout=60,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def list_splits(self) -> list[dict[str, Any]]:
        return list(self._request("GET", f"/{self._env_name}/splits"))

    def task_records(self, split: str) -> list[dict[str, Any]]:
        if split not in self._task_records:
            payload = self._request(
                "POST",
                f"/{self._env_name}/tasks",
                json={"split": split},
            )
            self._task_records[split] = [dict(task) for task in payload["tasks"]]
        return list(self._task_records[split])

    def task_indices(self, split: str) -> list[Any]:
        return [record["id"] for record in self.task_records(split)]

    def _find_task(self, task_id: Any) -> dict[str, Any]:
        for records in self._task_records.values():
            for record in records:
                if record["id"] == task_id:
                    return record
        raise KeyError(f"task {task_id!r} is not in any fetched split; call task_records first")

    def reset(self, task_idx: Any) -> Observation:
        result = self._client.reset(task_id=task_idx, **self._reset_options)
        observation = dict(result.observation)
        if observation.get("task_id") != task_idx:
            raise ValueError(
                f"OpenEnv reset identity mismatch: requested {task_idx!r}, "
                f"received {observation.get('task_id')!r}"
            )
        self._active_task = self._find_task(task_idx)
        self._observation = observation
        self._reward = 0.0 if result.reward is None else float(result.reward)
        return self._parse_observation(observation)

    def step(self, action: dict[str, Any]) -> StepResult:
        try:
            result = self._client.step(action)
        except RuntimeError as error:
            if "VALIDATION_ERROR" not in str(error):
                raise
            rendered = json.dumps(action, ensure_ascii=False, sort_keys=True)
            raise RuntimeError(
                f"{error}; server rejected action: {rendered}"
            ) from error
        observation = dict(result.observation)
        self._observation = observation
        self._reward = 0.0 if result.reward is None else float(result.reward)
        return StepResult(
            observation=self._parse_observation(observation),
            reward=self._reward,
            terminated=bool(observation["terminated"]),
            truncated=bool(observation["truncated"]),
        )

    def success(self) -> bool:
        if self._observation is None:
            raise RuntimeError("success() called before reset")
        return bool(self._observation["success"])

    def progress(self) -> float | None:
        if self._observation is None:
            raise RuntimeError("progress() called before reset")
        if "progress" not in self._observation:
            return None
        return float(self._observation["progress"])

    def diagnostics(self) -> dict[str, str]:
        if self._observation is None:
            return {}
        state = self._client.state()
        diagnostics = state.get("diagnostics", {})
        return {str(key): str(value) for key, value in diagnostics.items()}

    def close(self) -> None:
        if self._closed:
            raise RuntimeError("OpenEnv environment is already closed")
        self._client.close()
        self._closed = True

    def _parse_observation(self, raw: dict[str, Any]) -> Observation:
        """Every environment publishes text, goal, step_limit, success, terminated, and
        truncated on each observation. admissible_actions and progress are optional."""
        if self._active_task is None:
            raise RuntimeError("observation parsed before reset")
        return Observation(
            text=str(raw["text"]),
            admissible_actions=(
                list(raw["admissible_actions"]) if "admissible_actions" in raw else None
            ),
            goal=str(raw["goal"]),
            task_type=str(self._active_task["task_type"]),
            step_limit=int(raw["step_limit"]),
        )


def make_openenv(
    cfg: EnvCfg,
    task_records: dict[str, list[dict[str, Any]]] | None = None,
    *,
    reset_options: dict[str, Any] | None = None,
) -> OpenEnvEnvironment:
    """``reset_options`` defaults to ``cfg.reset_options``; SkillOpt training-batch rollouts pass
    the merged ``train_rollout_reset_options`` instead."""
    base_url = cfg.server_base
    scheme = urlsplit(base_url).scheme.lower()
    hostname = urlsplit(base_url).hostname
    if scheme not in {"https", "wss"} or hostname is None or not hostname.lower().endswith(".hf.space"):
        raise ValueError("OpenEnv requires an HTTPS/WSS Hugging Face Space endpoint")
    bearer_token = get_token()
    if not bearer_token:
        raise RuntimeError("OpenEnv requires Hugging Face authentication")
    headers = {"Authorization": f"Bearer {bearer_token}"}

    http_base = _http_base(base_url)
    metadata_response = _discovery_request("GET", http_base + "/metadata", headers=headers, timeout=60)
    metadata_response.raise_for_status()
    tools_response = _discovery_request("GET", http_base + "/tools", headers=headers, timeout=60)
    tools_response.raise_for_status()
    environments_response = _discovery_request(
        "GET", http_base + "/list_environments", headers=headers, timeout=60
    )
    environments_response.raise_for_status()
    names = environments_response.json()
    if not isinstance(names, list) or len(names) != 1:
        raise ValueError(f"OpenEnv endpoint must expose exactly one environment, got {names!r}")
    tools_payload = tools_response.json()
    if not isinstance(tools_payload, list) or not tools_payload:
        raise ValueError("OpenEnv endpoint must expose at least one native tool")
    tools: list[ToolSpec] = []
    seen_tool_names: set[str] = set()
    for payload in tools_payload:
        if not isinstance(payload, dict) or set(payload) != {
            "name",
            "description",
            "input_schema",
        }:
            raise ValueError(f"invalid native tool descriptor: {payload!r}")
        name = payload["name"]
        description = payload["description"]
        input_schema = payload["input_schema"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("native tool name must be non-empty")
        if name in seen_tool_names:
            raise ValueError(f"duplicate native tool name {name!r}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"native tool {name!r} has no description")
        if not isinstance(input_schema, dict):
            raise ValueError(f"native tool {name!r} input_schema must be an object")
        validator_for(input_schema).check_schema(input_schema)
        tools.append(ToolSpec(name, description, dict(input_schema)))
        seen_tool_names.add(name)

    def client_factory():
        return GenericOpenEnvClient(
            base_url=base_url,
            connect_timeout_s=cfg.timeout,
            message_timeout_s=cfg.timeout,
            websocket_ping_timeout_s=cfg.timeout,
            bearer_token=bearer_token,
        ).sync()

    return OpenEnvEnvironment(
        client_factory(),
        client_factory=client_factory,
        base_url=base_url,
        headers=headers,
        metadata=dict(metadata_response.json()),
        env_name=str(names[0]),
        tools=tools,
        task_records=task_records,
        reset_options=cfg.reset_options if reset_options is None else reset_options,
    )
