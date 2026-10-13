"""The environment contract the agent codes against.

The agent depends only on this interface + the typed `Observation`/`StepResult`, never on raw
HTTP dicts. Every benchmark implements `Env`, so the agent
and tracking are unchanged across environments.

Design follows the Gymnasium convention: `step` reports `terminated` (the task reached a real
terminal state) separately from `truncated` (an external step cutoff). `success()` is kept
separate from `terminated` — a task can terminate as a failure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    """One environment-owned native tool exposed to the actor."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class AgentContext:
    metadata: dict[str, Any]
    tools: tuple[ToolSpec, ...]


@dataclass(frozen=True)
class Observation:
    text: str  # what the agent reads
    admissible_actions: list[str] | None  # action hints (ALFWorld); None if unavailable
    goal: str
    task_type: str
    step_limit: int  # environment-protocol cap, must not exceed the configured safety cap


@dataclass(frozen=True)
class StepResult:
    observation: Observation
    reward: float
    terminated: bool  # task reached a terminal state (success or dead-end)
    truncated: bool  # external step cutoff

    @property
    def done(self) -> bool:
        return self.terminated or self.truncated


class Env(ABC):
    @abstractmethod
    def agent_context(self) -> AgentContext:
        """Return endpoint-discovered metadata and native tools."""

    @abstractmethod
    def reset(self, task_idx: int) -> Observation:
        """Load task `task_idx` and return the initial observation."""

    @abstractmethod
    def step(self, action: dict[str, Any]) -> StepResult:
        """Apply one JSON action conforming to the environment schema."""

    def step_tool(self, name: str, arguments: dict[str, Any]) -> StepResult:
        """Apply one native tool call through the generic OpenEnv wire envelope."""
        return self.step({"name": name, "arguments": arguments})

    @abstractmethod
    def success(self) -> bool:
        """True iff the task is currently solved."""

    @abstractmethod
    def progress(self) -> float | None:
        """Partial goal progress in [0, 1] for the current episode, or None when the
        environment only reports binary success. Environments with graded progress expose it
        so skill optimization can gate on it instead of the binary outcome."""

    def diagnostics(self) -> dict[str, str]:
        """Environment-specific extras for the reflection step, never shown to the acting model:
        e.g. a post-execution verification report with expected values, the exact target prompts,
        a data preview. Keys consumed by the SkillOpt adapter: ``verification`` (appended to the
        analysts' trajectory), ``spreadsheet_preview``, ``code``, ``fail_reason``. Empty by default."""
        return {}

    @abstractmethod
    def close(self) -> None:
        """Release server-side resources."""
