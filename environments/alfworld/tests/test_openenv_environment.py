"""Direct contract tests for the ALFWorld OpenEnv environment."""

from __future__ import annotations

from dataclasses import replace
from importlib.resources import files

import yaml

from alfworld_env.core import CoreObservation, CoreState, CoreStep
from alfworld_env.models import AlfWorldAction, AlfWorldObservation, AlfWorldState
from alfworld_env.server.environment import AlfWorldEnvironment


def test_upstream_time_limit_does_not_mask_openenv_truncation() -> None:
    config = yaml.safe_load(
        files("alfworld_env")
        .joinpath("assets", "config", "base_config.yaml")
        .read_text(encoding="utf-8")
    )

    assert config["dagger"]["training"]["max_nb_steps_per_episode"] == 51


class FakeCore:
    def __init__(self) -> None:
        self.reset_calls: list[int] = []
        self.step_calls: list[str] = []
        self.close_calls = 0
        self._state = CoreState(
            task_id=None,
            goal=None,
            reward=0.0,
            success=False,
            terminated=False,
            step_count=0,
            step_limit=50,
            closed=False,
        )

    def reset(self, task_id: int) -> CoreObservation:
        self.reset_calls.append(task_id)
        self._state = replace(
            self._state,
            task_id=task_id,
            goal="Put the apple on the table.",
        )
        return CoreObservation(
            task_id=task_id,
            text="You are in a kitchen.",
            goal="Put the apple on the table.",
            admissible_actions=("go to counter 1", "take apple 1 from counter 1"),
        )

    def step(self, action: str) -> CoreStep:
        self.step_calls.append(action)
        self._state = replace(
            self._state,
            reward=1.0,
            success=True,
            terminated=True,
            step_count=1,
        )
        return CoreStep(
            observation=CoreObservation(
                task_id=57,
                text="You put the apple on the table.",
                goal="Put the apple on the table.",
                admissible_actions=("look",),
            ),
            reward=1.0,
            terminated=True,
        )

    def state(self) -> CoreState:
        return self._state

    def close(self) -> None:
        self.close_calls += 1
        self._state = replace(self._state, closed=True)


def test_environment_delegates_typed_episode_and_admissible_actions() -> None:
    core = FakeCore()
    environment = AlfWorldEnvironment(core_factory=lambda: core)

    initial = environment.reset(task_id=57, episode_id="episode-57")

    assert core.reset_calls == [57]
    assert initial == AlfWorldObservation(
        task_id=57,
        text="You are in a kitchen.",
        goal="Put the apple on the table.",
        admissible_actions=["go to counter 1", "take apple 1 from counter 1"],
        success=False,
        terminated=False,
        truncated=False,
        done=False,
        reward=0.0,
    )

    result = environment.step(AlfWorldAction(command="take apple 1 from counter 1"))

    assert core.step_calls == ["take apple 1 from counter 1"]
    assert result.admissible_actions == ["look"]
    assert result.reward == 1.0
    assert result.success is True
    assert result.done is True
    assert environment.state == AlfWorldState(
        episode_id="episode-57",
        step_count=1,
        task_id=57,
        goal="Put the apple on the table.",
        reward=1.0,
        success=True,
        terminated=True,
        truncated=False,
        step_limit=50,
        closed=False,
    )

    environment.close()
    assert core.close_calls == 1
