"""Typed OpenEnv wire models for ALFWorld."""

from __future__ import annotations

from typing import Any

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, ConfigDict, Field, model_validator



class AlfWorldAct(BaseModel):
    """Execute one text command in ALFWorld."""

    model_config = ConfigDict(extra="forbid")

    command: str = Field(
        min_length=1,
        description=(
            "Exactly one ALFWorld text command, chosen from the current admissible actions "
            "(for example `go to countertop 1` or `take mug 1 from desk 1`)."
        ),
    )


class AlfWorldAction(Action, AlfWorldAct):
    """One executable ALFWorld text command."""

    @model_validator(mode="before")
    @classmethod
    def _accept_native_envelope(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        native_keys = {"name", "arguments"}
        if not native_keys.intersection(values):
            return values
        if set(values) != native_keys:
            raise ValueError(
                "ALFWorld native tool envelope must contain exactly "
                "'name' and 'arguments'"
            )
        action = native_tool_action(values["name"], values["arguments"])
        return action.model_dump()


def native_tool_specs() -> tuple[dict[str, Any], ...]:
    """Return the deterministic model-facing native tool catalog."""

    return (
        {
            "name": "act",
            "description": AlfWorldAct.__doc__,
            "input_schema": AlfWorldAct.model_json_schema(),
        },
    )


def native_tool_action(name: str, arguments: dict[str, Any]) -> AlfWorldAction:
    """Validate one native tool call and convert it to the OpenEnv action."""

    if name != "act":
        raise ValueError(f"unknown ALFWorld native tool: {name!r}")
    native_action = AlfWorldAct.model_validate(arguments)
    return AlfWorldAction(**native_action.model_dump())


class AlfWorldObservation(Observation):
    """Public ALFWorld observation with state-specific valid actions."""

    task_id: int
    text: str
    goal: str
    admissible_actions: list[str] = Field(min_length=1)
    success: bool
    terminated: bool
    truncated: bool
    step_limit: int = 50

    @model_validator(mode="before")
    @classmethod
    def _derive_done(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)
            values["done"] = bool(
                values.get("terminated", False) or values.get("truncated", False)
            )
        return values


class AlfWorldState(State):
    """Typed state for one connection-owned ALFWorld episode."""

    task_id: int | None = None
    goal: str | None = None
    reward: float = 0.0
    success: bool = False
    terminated: bool = False
    truncated: bool = False
    step_limit: int = 50
    closed: bool = False
