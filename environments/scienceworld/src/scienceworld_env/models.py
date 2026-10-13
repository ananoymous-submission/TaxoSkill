"""Typed OpenEnv wire models for ScienceWorld."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from openenv.core.env_server.types import Action, Observation, State


class ScienceWorldAct(BaseModel):
    """Execute one text command in ScienceWorld."""

    model_config = ConfigDict(extra="forbid")

    command: str = Field(
        min_length=1,
        description=(
            "Exactly one ScienceWorld text command from the action grammar in the "
            "environment description (for example `teleport to kitchen` or "
            "`use thermometer on unknown substance B`)."
        ),
    )


class ScienceWorldAction(Action, ScienceWorldAct):
    """One executable text command for the ScienceWorld engine."""

    @model_validator(mode="before")
    @classmethod
    def _unwrap_native_tool_call(cls, values: Any) -> Any:
        if isinstance(values, dict) and set(values) == {"name", "arguments"}:
            return native_tool_action(
                values["name"], values["arguments"]
            ).model_dump()
        return values


def native_tool_specs() -> tuple[dict[str, Any], ...]:
    """Return the ordered model-facing ScienceWorld native-tool catalog."""

    return (
        {
            "name": "act",
            "description": ScienceWorldAct.__doc__,
            "input_schema": ScienceWorldAct.model_json_schema(),
        },
    )


def native_tool_action(
    name: str, arguments: dict[str, Any]
) -> ScienceWorldAction:
    """Validate a native call and construct the OpenEnv transport action."""

    if name != "act":
        raise ValueError(f"unknown ScienceWorld native tool: {name!r}")
    call = ScienceWorldAct.model_validate(arguments)
    return ScienceWorldAction(**call.model_dump())


class ScienceWorldObservation(Observation):
    """Public observation returned after reset or an action."""

    task_id: int
    text: str
    goal: str
    score: float
    best_score: float
    progress: float = Field(ge=0.0, le=1.0)
    success: bool
    terminated: bool
    truncated: bool
    step_limit: int = 49

    @model_validator(mode="before")
    @classmethod
    def _derive_done(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)
            values["done"] = bool(
                values.get("terminated", False) or values.get("truncated", False)
            )
        return values


class ScienceWorldState(State):
    """Typed state for one connection-owned ScienceWorld episode."""

    task_id: int | None = None
    goal: str | None = None
    current_score: float = 0.0
    best_score: float = 0.0
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    success: bool = False
    terminated: bool = False
    truncated: bool = False
    step_limit: int = 49
    closed: bool = False
