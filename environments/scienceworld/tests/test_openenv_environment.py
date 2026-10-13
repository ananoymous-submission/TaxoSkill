"""Direct contract tests for the ScienceWorld OpenEnv environment."""

from __future__ import annotations

from dataclasses import replace

import pytest

from scienceworld_env.core import CoreObservation, CoreState, CoreStep
from scienceworld_env.models import (
    ScienceWorldAction,
    ScienceWorldObservation,
    ScienceWorldState,
)
from scienceworld_env.server.environment import ScienceWorldEnvironment


class FakeCore:
    def __init__(self) -> None:
        self.reset_calls: list[int] = []
        self.step_calls: list[str] = []
        self.close_calls = 0
        self._state = CoreState(
            task_id=None,
            goal=None,
            current_score=0.0,
            best_score=0.0,
            progress=0.0,
            success=False,
            terminated=False,
            step_count=0,
            step_limit=49,
            closed=False,
        )

    def reset(self, task_id: int) -> CoreObservation:
        self.reset_calls.append(task_id)
        self._state = CoreState(
            task_id=task_id,
            goal="Determine conductivity.",
            current_score=0.0,
            best_score=0.0,
            progress=0.0,
            success=False,
            terminated=False,
            step_count=0,
            step_limit=49,
            closed=False,
        )
        return CoreObservation(
            task_id=task_id,
            text="Initial room.",
            goal="Determine conductivity.",
            score=0.0,
        )

    def step(self, action: str) -> CoreStep:
        self.step_calls.append(action)
        self._state = CoreState(
            task_id=17,
            goal="Determine conductivity.",
            current_score=100.0,
            best_score=100.0,
            progress=1.0,
            success=True,
            terminated=True,
            step_count=1,
            step_limit=49,
            closed=False,
        )
        return CoreStep(
            observation=CoreObservation(
                task_id=17,
                text="Task complete.",
                goal="Determine conductivity.",
                score=100.0,
            ),
            reward=100.0,
            terminated=True,
        )

    def state(self) -> CoreState:
        return self._state

    def close(self) -> None:
        self.close_calls += 1
        self._state = replace(self._state, closed=True)


def test_environment_delegates_one_typed_episode_to_one_core() -> None:
    core = FakeCore()
    environment = ScienceWorldEnvironment(core_factory=lambda: core)

    initial = environment.reset(task_id=17, episode_id="episode-17")

    assert core.reset_calls == [17]
    assert initial == ScienceWorldObservation(
        task_id=17,
        text="Initial room.",
        goal="Determine conductivity.",
        score=0.0,
        best_score=0.0,
        progress=0.0,
        success=False,
        terminated=False,
        truncated=False,
        done=False,
        reward=0.0,
    )

    result = environment.step(ScienceWorldAction(command="put metal pot in blue box"))

    assert core.step_calls == ["put metal pot in blue box"]
    assert result == ScienceWorldObservation(
        task_id=17,
        text="Task complete.",
        goal="Determine conductivity.",
        score=100.0,
        best_score=100.0,
        progress=1.0,
        success=True,
        terminated=True,
        truncated=False,
        done=True,
        reward=100.0,
    )
    assert environment.state == ScienceWorldState(
        episode_id="episode-17",
        step_count=1,
        task_id=17,
        goal="Determine conductivity.",
        current_score=100.0,
        best_score=100.0,
        progress=1.0,
        success=True,
        terminated=True,
        truncated=False,
        step_limit=49,
        closed=False,
    )
    assert "task_type" not in ScienceWorldObservation.model_fields
    assert "split" not in ScienceWorldObservation.model_fields

    environment.close()
    assert core.close_calls == 1


def test_observation_derives_done_from_terminated_or_truncated() -> None:
    observation = ScienceWorldObservation(
        task_id=17,
        text="External limit reached.",
        goal="Determine conductivity.",
        score=50.0,
        best_score=50.0,
        progress=0.5,
        success=False,
        terminated=False,
        truncated=True,
        done=False,
        reward=0.0,
    )

    assert observation.done is True


def test_environment_uses_configured_default_task_for_generic_ui_reset() -> None:
    core = FakeCore()
    environment = ScienceWorldEnvironment(
        core_factory=lambda: core,
        default_task_id=17,
    )

    observation = environment.reset()

    assert core.reset_calls == [17]
    assert observation.task_id == 17


def test_environment_truncates_at_the_49_action_protocol_limit() -> None:
    class LimitCore(FakeCore):
        def __init__(self) -> None:
            super().__init__()
            self._state = replace(
                self._state,
                task_id=17,
                goal="Determine conductivity.",
                step_count=48,
            )

        def step(self, action: str) -> CoreStep:
            self.step_calls.append(action)
            self._state = replace(self._state, step_count=49)
            return CoreStep(
                observation=CoreObservation(
                    task_id=17,
                    text="Limit reached.",
                    goal="Determine conductivity.",
                    score=0.0,
                ),
                reward=0.0,
                terminated=False,
            )

    core = LimitCore()
    environment = ScienceWorldEnvironment(
        core_factory=lambda: core,  # type: ignore[arg-type]
    )

    observation = environment.step(ScienceWorldAction(command="look around"))

    assert observation.terminated is False
    assert observation.truncated is True
    assert observation.done is True
    assert environment.state.truncated is True
    with pytest.raises(RuntimeError, match="ScienceWorld episode has truncated"):
        environment.step(ScienceWorldAction(command="inventory"))
