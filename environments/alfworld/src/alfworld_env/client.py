"""Typed persistent-session client for the ALFWorld OpenEnv runtime."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlsplit

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import SecurityError

from alfworld_env.models import AlfWorldAction, AlfWorldObservation, AlfWorldState


class _AuthenticatedConnect(ws_connect):
    def process_redirect(self, exc: Exception) -> Exception | str:
        result = super().process_redirect(exc)
        if isinstance(result, str):
            return SecurityError("Authenticated WebSocket redirects are disabled")
        return result


def _authenticated_ws_connect(
    uri: str,
    *,
    bearer_token: str,
    **kwargs: Any,
):
    return _AuthenticatedConnect(
        uri,
        additional_headers={"Authorization": f"Bearer {bearer_token}"},
        **kwargs,
    )


class AlfWorldClient(EnvClient[AlfWorldAction, AlfWorldObservation, AlfWorldState]):
    """Typed WebSocket client for one connection-owned ALFWorld episode."""

    def __init__(
        self,
        *args: Any,
        bearer_token: str | None = None,
        **kwargs: Any,
    ) -> None:
        base_url = kwargs.get("base_url", args[0] if args else None)
        if bearer_token is not None:
            scheme = urlsplit(str(base_url)).scheme.lower()
            if scheme not in {"https", "wss"}:
                raise ValueError(
                    "Bearer authentication requires an HTTPS or WSS endpoint"
                )
        self._bearer_token = bearer_token
        super().__init__(*args, **kwargs)

    async def _connect_async(self) -> AlfWorldClient:
        if self._bearer_token is None:
            await super()._connect_async()
            return self
        if self._ws is not None:
            if self._ws_loop is asyncio.get_running_loop():
                return self
            self._ws = None
            self._ws_loop = None

        try:
            self._start_provider_if_needed()
        except Exception:
            await self.close()
            raise

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
            raise ConnectionError(
                f"Failed to connect to {self._ws_url}: {error}"
            ) from error
        return self

    def _step_payload(self, action: AlfWorldAction) -> dict[str, Any]:
        return action.model_dump()

    def _parse_result(
        self,
        payload: dict[str, Any],
    ) -> StepResult[AlfWorldObservation]:
        observation_data = dict(payload.get("observation", {}))
        reward_value = payload.get("reward")
        reward = None if reward_value is None else float(reward_value)
        metadata = payload.get("metadata", observation_data.get("metadata"))
        observation_data.update(
            reward=reward,
            done=bool(payload.get("done", False)),
            metadata={} if metadata is None else metadata,
        )
        observation = AlfWorldObservation.model_validate(observation_data)
        return StepResult(
            observation=observation,
            reward=reward,
            done=observation.done,
            metadata=metadata,
        )

    def _parse_state(self, payload: dict[str, Any]) -> AlfWorldState:
        return AlfWorldState.model_validate(payload)
