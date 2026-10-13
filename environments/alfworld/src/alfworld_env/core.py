"""Framework-neutral ALFWorld lifecycle and benchmark semantics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from alfworld_env.catalog import AlfWorldTask, get_task


_GOAL_MARKER = "Your task is to:"


@dataclass(frozen=True, slots=True)
class BackendObservation:
    """Normalized transition returned by the private ALFWorld backend."""

    text: str
    admissible_actions: tuple[str, ...]
    runtime_task_type: str
    reward: float
    terminated: bool


class _AlfWorldBackend(Protocol):
    def reset(self, gamefile: str) -> BackendObservation: ...

    def step(self, action: str) -> BackendObservation: ...

    def close(self) -> None: ...


_BackendFactory = Callable[[], _AlfWorldBackend]


def _default_backend_factory() -> _AlfWorldBackend:
    from alfworld_env.process_backend import ProcessAlfWorldBackend

    return ProcessAlfWorldBackend()


@dataclass(frozen=True, slots=True)
class CoreObservation:
    """Agent-facing ALFWorld observation from one backend state."""

    task_id: int
    text: str
    goal: str
    admissible_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CoreStep:
    """One state-changing ALFWorld transition."""

    observation: CoreObservation
    reward: float
    terminated: bool


@dataclass(frozen=True, slots=True)
class CoreState:
    """Immutable episode state for introspection and transport adapters."""

    task_id: int | None
    goal: str | None
    reward: float
    success: bool
    terminated: bool
    step_count: int
    step_limit: int
    closed: bool


def _parse_goal(text: str, task_id: int) -> str:
    if _GOAL_MARKER not in text:
        raise ValueError(f"ALFWorld task {task_id} has no goal marker")
    goal = text.split(_GOAL_MARKER, 1)[1].strip()
    if not goal:
        raise ValueError(f"ALFWorld task {task_id} has an empty goal")
    return goal


def _validate_actions(actions: tuple[str, ...], task_id: int) -> None:
    if not actions:
        raise ValueError(f"ALFWorld task {task_id} returned no admissible actions")
    if any(not action.strip() for action in actions):
        raise ValueError(f"ALFWorld task {task_id} returned an invalid admissible action")


def _validate_identity(task: AlfWorldTask, runtime_task_type: str) -> None:
    resolved_folder = runtime_task_type.split("/", 1)[0]
    if not (
        resolved_folder == task.task_type
        or resolved_folder.startswith(task.task_type + "-")
    ):
        raise ValueError(
            f"ALFWorld task {task.task_id} resolved as {resolved_folder!r}, "
            f"expected {task.task_type!r}"
        )


class AlfWorldCore:
    """Own one stateful ALFWorld text backend for one complete episode."""

    def __init__(
        self,
        backend_factory: _BackendFactory = _default_backend_factory,
    ) -> None:
        self._backend = backend_factory()
        self._task_id: int | None = None
        self._goal: str | None = None
        self._reward = 0.0
        self._terminated = False
        self._step_count = 0
        self._closed = False

    def reset(self, task_id: int) -> CoreObservation:
        self._ensure_open()
        task = get_task(task_id)
        result = self._backend.reset(task.gamefile)
        _validate_identity(task, result.runtime_task_type)
        _validate_actions(result.admissible_actions, task_id)
        goal = _parse_goal(result.text, task_id)
        self._task_id = task_id
        self._goal = goal
        self._reward = float(result.reward)
        self._terminated = bool(result.terminated)
        self._step_count = 0
        return CoreObservation(
            task_id=task_id,
            text=result.text,
            goal=goal,
            admissible_actions=result.admissible_actions,
        )

    def step(self, action: str) -> CoreStep:
        self._ensure_open()
        if self._task_id is None or self._goal is None:
            raise RuntimeError("ALFWorld core must be reset before step")
        if self._terminated:
            raise RuntimeError("ALFWorld episode has terminated")
        task = get_task(self._task_id)
        result = self._backend.step(action)
        _validate_identity(task, result.runtime_task_type)
        _validate_actions(result.admissible_actions, self._task_id)
        self._reward = float(result.reward)
        self._terminated = bool(result.terminated)
        self._step_count += 1
        return CoreStep(
            observation=CoreObservation(
                task_id=self._task_id,
                text=result.text,
                goal=self._goal,
                admissible_actions=result.admissible_actions,
            ),
            reward=self._reward,
            terminated=self._terminated,
        )

    def state(self) -> CoreState:
        return CoreState(
            task_id=self._task_id,
            goal=self._goal,
            reward=self._reward,
            success=self._reward == 1.0,
            terminated=self._terminated,
            step_count=self._step_count,
            step_limit=50,
            closed=self._closed,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._backend.close()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("ALFWorld core is closed")
