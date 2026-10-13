"""Framework-neutral ScienceWorld simulator lifecycle and benchmark semantics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from scienceworld_env.catalog import ScienceWorldTask, get_task


class _ScienceWorldInstance(Protocol):
    """The portion of the upstream ScienceWorld instance used by the core."""

    def load(
        self,
        task_name: str,
        variation_idx: int,
        simplification: str,
        generate_gold_path: bool,
    ) -> None: ...

    def reset(self) -> tuple[str, dict[str, Any]]: ...

    def step(self, action: str) -> tuple[str, float, bool, dict[str, Any]]: ...

    def close(self) -> None: ...


_ScienceWorldFactory = Callable[[], _ScienceWorldInstance]


@dataclass(frozen=True, slots=True)
class CoreObservation:
    """Agent-facing text and benchmark score from one simulator state."""

    task_id: int
    text: str
    goal: str
    score: float


@dataclass(frozen=True, slots=True)
class CoreStep:
    """One state-changing ScienceWorld transition."""

    observation: CoreObservation
    reward: float
    terminated: bool


@dataclass(frozen=True, slots=True)
class CoreState:
    """Immutable episode state for introspection and transport adapters."""

    task_id: int | None
    goal: str | None
    current_score: float
    best_score: float
    progress: float
    success: bool
    terminated: bool
    step_count: int
    step_limit: int
    closed: bool


def _default_scienceworld_factory() -> _ScienceWorldInstance:
    from scienceworld import ScienceWorldEnv  # type: ignore[import-not-found]

    return ScienceWorldEnv()


class ScienceWorldCore:
    """Own one upstream ScienceWorld instance for one complete episode."""

    def __init__(
        self,
        scienceworld_factory: _ScienceWorldFactory = _default_scienceworld_factory,
    ) -> None:
        self._scienceworld = scienceworld_factory()
        self._task_id: int | None = None
        self._runtime_task_name: str | None = None
        self._goal: str | None = None
        self._current_score = 0.0
        self._best_score = 0.0
        self._terminated = False
        self._step_count = 0
        self._closed = False

    def reset(self, task_id: int) -> CoreObservation:
        self._ensure_open()
        task = get_task(task_id)
        self._scienceworld.load(task.task_type, task.variation_idx, "easy", False)
        runtime_task_name = str(
            getattr(self._scienceworld, "taskName", task.task_type)
        )
        text, info = self._scienceworld.reset()
        self._validate_identity(task, runtime_task_name, info)
        goal = str(info["taskDesc"])
        prefix = "Task Description:"
        if goal.startswith(prefix):
            goal = goal[len(prefix) :].lstrip()
        if not goal.strip():
            raise ValueError(f"ScienceWorld task {task_id} has an empty description")
        score = float(info["score"])
        self._task_id = task.task_id
        self._runtime_task_name = runtime_task_name
        self._goal = goal
        self._current_score = score
        self._best_score = score
        self._terminated = False
        self._step_count = 0
        return CoreObservation(
            task_id=task.task_id,
            text=str(text),
            goal=goal,
            score=score,
        )

    @staticmethod
    def _validate_identity(
        task: ScienceWorldTask,
        runtime_task_name: str,
        info: dict[str, Any],
    ) -> None:
        actual_name = info.get("taskName")
        actual_variation = info.get("variationIdx")
        if actual_name != runtime_task_name or actual_variation != task.variation_idx:
            raise ValueError(
                "ScienceWorld runtime identity mismatch: expected "
                f"{runtime_task_name} variation {task.variation_idx}, got "
                f"{actual_name} variation {actual_variation}"
            )

    def step(self, action: str) -> CoreStep:
        self._ensure_open()
        if (
            self._task_id is None
            or self._runtime_task_name is None
            or self._goal is None
        ):
            raise RuntimeError("ScienceWorld core must be reset before step")
        if self._terminated:
            raise RuntimeError("ScienceWorld episode has terminated")
        text, reward, terminated, info = self._scienceworld.step(action)
        self._validate_identity(
            get_task(self._task_id),
            self._runtime_task_name,
            info,
        )
        score = float(info["score"])
        self._current_score = score
        self._best_score = max(self._best_score, score)
        self._terminated = bool(terminated)
        self._step_count += 1
        return CoreStep(
            observation=CoreObservation(
                task_id=self._task_id,
                text=str(text),
                goal=self._goal,
                score=score,
            ),
            reward=float(reward),
            terminated=self._terminated,
        )

    def state(self) -> CoreState:
        progress = max(0.0, min(1.0, self._best_score / 100.0))
        return CoreState(
            task_id=self._task_id,
            goal=self._goal,
            current_score=self._current_score,
            best_score=self._best_score,
            progress=progress,
            success=self._best_score >= 100.0,
            terminated=self._terminated,
            step_count=self._step_count,
            step_limit=49,
            closed=self._closed,
        )

    def close(self) -> None:
        """Release the owned simulator exactly once."""

        if self._closed:
            return
        self._scienceworld.close()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("ScienceWorld core is closed")
