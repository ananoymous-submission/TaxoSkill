"""Genuine OpenEnv adapter around one ScienceWorld core instance."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

from scienceworld_env.catalog import get_split
from scienceworld_env.core import CoreObservation, ScienceWorldCore
from scienceworld_env.interface import environment_description
from scienceworld_env.models import (
    ScienceWorldAction,
    ScienceWorldObservation,
    ScienceWorldState,
)


_CoreFactory = Callable[[], ScienceWorldCore]


class ScienceWorldEnvironment(
    Environment[ScienceWorldAction, ScienceWorldObservation, ScienceWorldState]
):
    """One connection-owned, typed ScienceWorld OpenEnv environment."""

    SUPPORTS_CONCURRENT_SESSIONS = True
    REQUIRES_SINGLE_THREAD_EXECUTOR = False

    def __init__(
        self,
        core_factory: _CoreFactory = ScienceWorldCore,
        *,
        default_task_id: int | None = None,
    ) -> None:
        super().__init__()
        self._core_factory = core_factory
        self._core: ScienceWorldCore | None = None
        self._default_task_id = default_task_id
        self._episode_id: str | None = None
        self._truncated = False
        self._closed = False

    def _get_core(self) -> ScienceWorldCore:
        if self._closed:
            raise RuntimeError("ScienceWorld environment is closed")
        if self._core is None:
            self._core = self._core_factory()
        return self._core

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="ScienceWorld",
            description=environment_description(),
            version="0.1.0",
            documentation_url="https://github.com/allenai/ScienceWorld",
        )

    def list_splits(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "role": get_split(name).role,
                "num_tasks": len(get_split(name).tasks),
                "source_revision": get_split(name).source_revision,
                "sha256": get_split(name).sha256,
            }
            for name in ("development", "test_seen", "test_unseen")
        ]

    def list_tasks(self, split: str) -> list[dict[str, Any]]:
        task_split = get_split(split)
        return [
            {
                "id": task.task_id,
                "instruction": task.instruction,
                "task_type": task.task_type,
                "split": task_split.role,
                "source_revision": task_split.source_revision,
                "catalog_sha256": task_split.sha256,
            }
            for task in task_split.tasks
        ]

    def num_tasks(self, split: str) -> int:
        return len(get_split(split).tasks)

    def get_task(self, split: str, index: int) -> dict[str, Any]:
        tasks = self.list_tasks(split)
        try:
            return tasks[index]
        except IndexError as error:
            raise IndexError(f"ScienceWorld {split} task index out of range: {index}") from error

    def get_task_range(
        self,
        split: str,
        start: int | None = None,
        stop: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.list_tasks(split)[slice(start, stop)]

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        *,
        task_id: int | None = None,
        **kwargs: Any,
    ) -> ScienceWorldObservation:
        del seed, kwargs
        resolved_task_id = self._default_task_id if task_id is None else task_id
        if resolved_task_id is None:
            raise ValueError("ScienceWorld reset requires task_id")
        core_observation = self._get_core().reset(resolved_task_id)
        self._episode_id = episode_id or str(uuid4())
        self._truncated = False
        return self._observation(core_observation, reward=0.0)

    def step(
        self,
        action: ScienceWorldAction,
        timeout_s: float | None = None,
        **kwargs: Any,
    ) -> ScienceWorldObservation:
        del timeout_s, kwargs
        if self._truncated:
            raise RuntimeError("ScienceWorld episode has truncated")
        core = self._get_core()
        transition = core.step(action.command)
        state = core.state()
        self._truncated = (
            not transition.terminated and state.step_count >= state.step_limit
        )
        return self._observation(
            transition.observation,
            reward=transition.reward,
        )

    @property
    def state(self) -> ScienceWorldState:
        if self._core is None:
            return ScienceWorldState(
                episode_id=self._episode_id,
                step_count=0,
                closed=self._closed,
            )
        core_state = self._core.state()
        return ScienceWorldState(
            episode_id=self._episode_id,
            step_count=core_state.step_count,
            task_id=core_state.task_id,
            goal=core_state.goal,
            current_score=core_state.current_score,
            best_score=core_state.best_score,
            progress=core_state.progress,
            success=core_state.success,
            terminated=core_state.terminated,
            truncated=self._truncated,
            step_limit=core_state.step_limit,
            closed=core_state.closed,
        )

    def close(self) -> None:
        if self._closed:
            return
        if self._core is not None:
            self._core.close()
        self._closed = True

    def _observation(
        self,
        observation: CoreObservation,
        *,
        reward: float,
    ) -> ScienceWorldObservation:
        state = self._get_core().state()
        return ScienceWorldObservation(
            task_id=observation.task_id,
            text=observation.text,
            goal=observation.goal,
            score=observation.score,
            best_score=state.best_score,
            progress=state.progress,
            success=state.success,
            terminated=state.terminated,
            truncated=self._truncated,
            done=state.terminated or self._truncated,
            reward=reward,
        )
