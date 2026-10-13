"""One project-owned client for every configured LLM call.

`Model` wraps one plain OpenAI Chat Completions client. `act()` is one ReAct step with the
environment's native tools; `chat()` is one text request (taxonomy). Provider differences live
only in `_request_fields`. The SDK retries transport faults up to `max_retries`; every other
error raises. Responses are not re-validated against a strict schema, so provider-specific
extra fields never fail a step.

Provider facts baked in (verified September 2026):
  * DeepSeek V4 has thinking OFF by default; it is toggled through ``extra_body.thinking``.
    Thinking mode rejects ``tool_choice="required"``, so thinking actors use ``auto``.
    The chain-of-thought arrives on ``reasoning_content``.
  * OpenAI-compatible servers (vLLM) differ per model in how thinking is controlled, so each
    model profile declares ``thinking_control``: ``enable_thinking`` for models with a
    ``chat_template_kwargs.enable_thinking`` switch (Qwen), ``always_on`` for models whose chat
    template always opens a think block and only accept ``reasoning_effort`` (GLM-5.3).
    Sending ``enable_thinking=false`` to an always-on model leaks its reasoning into ``content``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any

import jsonschema
from openai import OpenAI
from openai.resources.chat.completions import Completions
from skillopt.model import configure_openai_compatible

from taxoskill.config import ModelCfg, ModelProfileCfg, RunCfg, SkillOptModelCfg, SubModelCfg
from taxoskill.environment import ToolSpec


@dataclass(frozen=True)
class ToolCall:
    """Normalized result of one actor step.

    ``failure`` is set only for model-behaviour faults the loop feeds back to the model: no
    tool call, completion budget exhausted, unknown tool, or arguments that are not a JSON
    object or do not satisfy the tool schema. Transport and provider errors raise instead.
    """

    name: str | None
    arguments: dict[str, Any] | None
    reasoning: str
    raw_response: str
    input_tokens: int
    output_tokens: int
    failure: str | None = None
    error: str = ""


def _request_fields(profile: ModelProfileCfg, policy: SubModelCfg | SkillOptModelCfg) -> dict[str, Any]:
    """Provider-specific Chat Completions fields. The only place providers differ."""
    fields: dict[str, Any] = {
        "temperature": policy.temperature,
        "max_tokens": policy.max_tokens,
    }
    if profile.backend == "deepseek":
        if policy.thinking:
            if policy.reasoning_effort not in {"high", "max"}:
                raise ValueError("DeepSeek thinking supports reasoning_effort high or max")
            fields["tool_choice"] = "auto"
            fields["extra_body"] = {
                "thinking": {"type": "enabled"},
                "reasoning_effort": policy.reasoning_effort,
            }
        else:
            fields["tool_choice"] = "required"
            fields["extra_body"] = {"thinking": {"type": "disabled"}}
        return fields
    if profile.backend == "openai_compatible":
        fields["tool_choice"] = "required"
        if profile.thinking_control == "enable_thinking":
            fields["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": policy.thinking}
            }
            if policy.thinking:
                fields["reasoning_effort"] = policy.reasoning_effort
            return fields
        if profile.thinking_control == "always_on":
            if not policy.thinking:
                raise ValueError(
                    f"model {profile.model!r} cannot disable thinking; "
                    "set thinking=true and choose reasoning_effort"
                )
            fields["reasoning_effort"] = policy.reasoning_effort
            return fields
        if profile.thinking_control == "openrouter":
            # OpenRouter normalizes one `reasoning` object across upstream providers; the
            # `provider` object pins a single upstream and forbids silent fallbacks.
            reasoning: dict[str, Any] = {"enabled": policy.thinking}
            if policy.thinking:
                reasoning["effort"] = policy.reasoning_effort
            fields["extra_body"] = {
                "reasoning": reasoning,
                "provider": {"order": [profile.provider], "allow_fallbacks": False},
            }
            return fields
        raise ValueError(f"unsupported thinking_control {profile.thinking_control!r}")
    raise ValueError(f"unsupported LLM backend {profile.backend!r}")


REASONING_FIELD = "reasoning"
_REASONING_SCHEMA = {
    "type": "string",
    "description": (
        "One or two sentences on why this is the right next action, written before "
        "deciding the other arguments."
    ),
}


def _with_reasoning(schema: dict[str, Any]) -> dict[str, Any]:
    """Add the agent-side reasoning argument to an environment tool schema.

    Every tool call carries a short written reason, so each trajectory step has one even when
    the provider returns no native chain of thought. The environments never see this field:
    `act()` strips it from the returned arguments before validating them against the
    environment's own schema.
    """
    if REASONING_FIELD in schema.get("properties", {}):
        raise ValueError(f"environment tool already defines a {REASONING_FIELD!r} argument")
    return {
        **schema,
        "properties": {REASONING_FIELD: _REASONING_SCHEMA, **schema.get("properties", {})},
        "required": [REASONING_FIELD, *schema.get("required", [])],
    }


def _function_tools(
    tools: tuple[ToolSpec, ...], *, with_reasoning: bool
) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": (
                    _with_reasoning(tool.input_schema) if with_reasoning else tool.input_schema
                ),
            },
        }
        for tool in tools
    ]


class Model:
    """One configured model: a profile (identity, endpoint) plus a policy (sampling, thinking)."""

    def __init__(
        self, profile: ModelProfileCfg, policy: SubModelCfg, runtime: ModelCfg
    ) -> None:
        self.profile = profile
        self.policy = policy
        self._client = OpenAI(
            base_url=profile.resolved_base_url,
            api_key=profile.resolved_api_key,
            timeout=runtime.timeout,
            max_retries=runtime.max_retries,
        )
        self._fields = _request_fields(profile, policy)

    def _create(self, system: str, user: str, **extra: Any) -> Any:
        fields = dict(self._fields)
        if "tools" not in extra:
            fields.pop("tool_choice")
        response = self._client.chat.completions.create(
            model=self.profile.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **fields,
            **extra,
        )
        if len(response.choices) != 1:
            raise RuntimeError(
                f"model request must return exactly one choice, got {len(response.choices)}"
            )
        if response.usage is None:
            raise RuntimeError("model response carries no token usage")
        return response

    def chat(self, system: str, user: str) -> str:
        """One text request. Raises on an empty body."""
        content = self._create(system, user).choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("model returned an empty response")
        return content

    def act(
        self,
        system: str,
        user: str,
        tools: tuple[ToolSpec, ...],
        *,
        with_reasoning: bool,
    ) -> ToolCall:
        """One ReAct step: return exactly one validated native tool call.

        ``with_reasoning`` adds the written-rationale argument to every tool (``react.reasoning``);
        it is stripped before the arguments are validated against the environment's schema.
        """
        if not tools:
            raise ValueError("act requires at least one environment tool")
        response = self._create(
            system,
            user,
            tools=_function_tools(tools, with_reasoning=with_reasoning),
            parallel_tool_calls=False,
        )
        choice = response.choices[0]
        message = choice.message
        raw_response = response.model_dump_json(warnings=False)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        reasoning_content = (message.model_extra or {}).get("reasoning_content")
        if reasoning_content is not None and not isinstance(reasoning_content, str):
            raise RuntimeError(
                f"reasoning_content must be a string, got {type(reasoning_content).__name__}"
            )
        reasoning = "\n".join(
            part.strip()
            for part in (reasoning_content or "", message.content or "")
            if part and part.strip()
        )

        def failed(category: str, error: str) -> ToolCall:
            return ToolCall(
                name=None,
                arguments=None,
                reasoning=reasoning,
                raw_response=raw_response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                failure=category,
                error=error,
            )

        if choice.finish_reason == "length":
            return failed(
                "length_limit",
                "the response hit the completion token limit before a tool call was emitted",
            )
        calls = message.tool_calls or []
        if not calls:
            return failed("no_tool_call", "the response contains no tool call")
        # Environment actions are stateful: execute only the first ordered call and let the
        # actor reconsider after observing its result.
        call = calls[0]
        if call.type != "function":
            raise RuntimeError(f"unsupported tool call type {call.type!r}")
        try:
            arguments = json.loads(call.function.arguments)
        except json.JSONDecodeError as error:
            return failed("malformed_arguments", f"arguments are not valid JSON: {error}")
        if not isinstance(arguments, dict):
            return failed(
                "malformed_arguments",
                f"arguments must be a JSON object, got {type(arguments).__name__}",
            )
        if with_reasoning:
            written = arguments.pop(REASONING_FIELD, None)
            if not isinstance(written, str) or not written.strip():
                return failed(
                    "invalid_arguments", f"{REASONING_FIELD}: a non-empty string is required"
                )
            reasoning = "\n".join(part for part in (reasoning, written.strip()) if part)
        matching = [tool for tool in tools if tool.name == call.function.name]
        if not matching:
            return failed("unknown_tool", f"unknown native tool {call.function.name!r}")
        try:
            jsonschema.validate(arguments, matching[0].input_schema)
        except jsonschema.ValidationError as error:
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            return failed("invalid_arguments", f"{path}: {error.message}")
        return ToolCall(
            name=call.function.name,
            arguments=arguments,
            reasoning=reasoning,
            raw_response=raw_response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def actor_model(cfg: RunCfg) -> Model:
    """The rollout actor for one run configuration."""
    return Model(cfg.actor_model, cfg.model.rollout, cfg.model)


def configure_skillopt_backend(cfg: RunCfg) -> None:
    """Configure official SkillOpt from the same role-specific model profiles."""
    optimizer = cfg.optimizer_model
    actor = cfg.actor_model
    configure_openai_compatible(
        optimizer_base_url=optimizer.resolved_base_url,
        optimizer_api_key=optimizer.resolved_api_key,
        optimizer_model=optimizer.model,
        target_base_url=actor.resolved_base_url,
        target_api_key=actor.resolved_api_key,
        target_model=actor.model,
        temperature=cfg.skillopt.optimizer.temperature,
        timeout_seconds=cfg.model.timeout,
        max_tokens=cfg.skillopt.optimizer.max_tokens,
    )


@contextmanager
def optimizer_request_context(cfg: RunCfg) -> Iterator[None]:
    """Apply the optimizer profile's provider-specific request fields."""
    profile = cfg.optimizer_model
    policy = cfg.skillopt.optimizer
    request_fields = _request_fields(profile, policy)
    request_fields.pop("tool_choice", None)
    original_create = Completions.create

    @wraps(original_create)
    def create_with_thinking(self: Completions, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("model") == profile.model:
            if "extra_body" in kwargs:
                raise ValueError(
                    "SkillOpt optimizer request already contains extra_body; "
                    "refusing to overwrite it"
                )
            for key, value in request_fields.items():
                if key == "extra_body":
                    kwargs[key] = value
                else:
                    kwargs.setdefault(key, value)
        return original_create(self, *args, **kwargs)

    Completions.create = create_with_thinking
    try:
        yield
    finally:
        if Completions.create is not create_with_thinking:
            raise RuntimeError("OpenAI Completions.create changed during SkillOpt run")
        Completions.create = original_create


def run_optimizer_preflight(cfg: RunCfg) -> dict[str, int]:
    """Make one optimizer call and require its configured reasoning response."""
    profile = cfg.optimizer_model
    client = OpenAI(
        base_url=profile.resolved_base_url,
        api_key=profile.resolved_api_key,
        timeout=cfg.model.timeout,
    )
    response = client.chat.completions.create(
        model=profile.model,
        messages=[
            {
                "role": "system",
                "content": "You are verifying a skill-optimization model connection.",
            },
            {
                "role": "user",
                "content": "Think briefly, then reply with exactly: PREFLIGHT_OK",
            },
        ],
        max_tokens=512,
    )
    if len(response.choices) != 1:
        raise RuntimeError("SkillOpt optimizer preflight must return exactly one choice")
    message = response.choices[0].message
    reasoning_key = "reasoning" if profile.thinking_control == "openrouter" else "reasoning_content"
    if message.model_extra is None or reasoning_key not in message.model_extra:
        raise RuntimeError(
            "SkillOpt optimizer preflight response has no reasoning_content field"
        )
    reasoning = message.model_extra[reasoning_key]
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise RuntimeError(
            "SkillOpt optimizer preflight returned no reasoning_content; "
            "thinking mode is not verified"
        )
    if message.content is None or message.content.strip() != "PREFLIGHT_OK":
        raise RuntimeError(
            "SkillOpt optimizer preflight returned an unexpected final response"
        )
    return {
        "reasoning_characters": len(reasoning),
        "response_characters": len(message.content),
    }
