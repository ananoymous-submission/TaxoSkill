"""Behavioral contract for the framework-neutral ALFWorld core."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest

from alfworld_env.core import (
    AlfWorldCore,
    BackendObservation,
    CoreObservation,
    CoreState,
    CoreStep,
    _default_backend_factory,
)


def test_default_backend_factory_lazily_constructs_process_backend(monkeypatch) -> None:
    module = ModuleType("alfworld_env.process_backend")

    class FakeProcessBackend:
        pass

    setattr(module, "ProcessAlfWorldBackend", FakeProcessBackend)
    monkeypatch.setitem(sys.modules, "alfworld_env.process_backend", module)

    assert isinstance(_default_backend_factory(), FakeProcessBackend)


class FakeBackend:
    def __init__(self) -> None:
        self.reset_calls: list[str] = []
        self.step_calls: list[str] = []
        self.step_results: list[BackendObservation] = []
        self.reset_result = BackendObservation(
            text=(
                "You are in a bedroom.\n\n"
                "Your task is to: Pick up the alarm clock and turn on the lamp."
            ),
            admissible_actions=("go to desk 1", "take alarmclock 1 from desk 1"),
            runtime_task_type=(
                "look_at_obj_in_light-AlarmClock-None-DeskLamp-301/"
                "trial_T20190907_174127_043461"
            ),
            reward=0.0,
            terminated=False,
        )
        self.closed = False
        self.close_calls = 0

    def reset(self, gamefile: str) -> BackendObservation:
        self.reset_calls.append(gamefile)
        return self.reset_result

    def step(self, action: str) -> BackendObservation:
        self.step_calls.append(action)
        if not self.step_results:
            raise AssertionError(f"unexpected step: {action}")
        return self.step_results.pop(0)

    def close(self) -> None:
        self.closed = True
        self.close_calls += 1


def test_reset_selects_the_exact_frozen_game_and_parses_the_goal() -> None:
    backend = FakeBackend()
    core = AlfWorldCore(backend_factory=lambda: backend)

    observation = core.reset(191)

    assert backend.reset_calls == [
        "json_2.1.1/train/look_at_obj_in_light-AlarmClock-None-DeskLamp-301/"
        "trial_T20190907_174127_043461/game.tw-pddl"
    ]
    assert observation == CoreObservation(
        task_id=191,
        text=(
            "You are in a bedroom.\n\n"
            "Your task is to: Pick up the alarm clock and turn on the lamp."
        ),
        goal="Pick up the alarm clock and turn on the lamp.",
        admissible_actions=("go to desk 1", "take alarmclock 1 from desk 1"),
    )


def test_step_preserves_actions_reward_success_and_terminal_state() -> None:
    backend = FakeBackend()
    task_type = (
        "look_at_obj_in_light-AlarmClock-None-DeskLamp-301/"
        "trial_T20190907_174127_043461"
    )
    backend.step_results = [
        BackendObservation(
            text="You arrive at the desk.",
            admissible_actions=("take alarmclock 1 from desk 1",),
            runtime_task_type=task_type,
            reward=0.0,
            terminated=False,
        ),
        BackendObservation(
            text="You turn on the lamp while holding the alarm clock.",
            admissible_actions=("look",),
            runtime_task_type=task_type,
            reward=1.0,
            terminated=True,
        ),
    ]
    core = AlfWorldCore(backend_factory=lambda: backend)
    core.reset(191)

    first = core.step("go to desk 1")

    assert first == CoreStep(
        observation=CoreObservation(
            task_id=191,
            text="You arrive at the desk.",
            goal="Pick up the alarm clock and turn on the lamp.",
            admissible_actions=("take alarmclock 1 from desk 1",),
        ),
        reward=0.0,
        terminated=False,
    )
    assert core.state() == CoreState(
        task_id=191,
        goal="Pick up the alarm clock and turn on the lamp.",
        reward=0.0,
        success=False,
        terminated=False,
        step_count=1,
        step_limit=50,
        closed=False,
    )

    final = core.step("take alarmclock 1 from desk 1")
    assert final.reward == 1.0
    assert final.terminated is True
    assert core.state().success is True
    assert core.state().step_count == 2


def test_uninitialized_and_closed_core_fail_loudly_and_cleanup_once() -> None:
    backend = FakeBackend()
    core = AlfWorldCore(backend_factory=lambda: backend)

    assert core.state() == CoreState(
        task_id=None,
        goal=None,
        reward=0.0,
        success=False,
        terminated=False,
        step_count=0,
        step_limit=50,
        closed=False,
    )
    with pytest.raises(RuntimeError, match="must be reset before step"):
        core.step("look")
    with pytest.raises(ValueError, match="unknown ALFWorld task ID: 56"):
        core.reset(56)

    core.close()
    core.close()

    assert backend.close_calls == 1
    assert core.state().closed is True
    with pytest.raises(RuntimeError, match="ALFWorld core is closed"):
        core.reset(191)


@pytest.mark.parametrize(
    ("result", "message"),
    [
        (
            BackendObservation(
                text="No task marker.",
                admissible_actions=("look",),
                runtime_task_type="look_at_obj_in_light-fixture/trial",
                reward=0.0,
                terminated=False,
            ),
            "has no goal marker",
        ),
        (
            BackendObservation(
                text="Your task is to: Test.",
                admissible_actions=(),
                runtime_task_type="look_at_obj_in_light-fixture/trial",
                reward=0.0,
                terminated=False,
            ),
            "returned no admissible actions",
        ),
        (
            BackendObservation(
                text="Your task is to: Test.",
                admissible_actions=("look",),
                runtime_task_type="pick_and_place_simple-fixture/trial",
                reward=0.0,
                terminated=False,
            ),
            "resolved as",
        ),
    ],
)
def test_reset_rejects_invalid_backend_identity_and_observations(
    result: BackendObservation,
    message: str,
) -> None:
    backend = FakeBackend()
    backend.reset_result = result
    core = AlfWorldCore(backend_factory=lambda: backend)

    with pytest.raises(ValueError, match=message):
        core.reset(191)
    assert core.state().task_id is None
