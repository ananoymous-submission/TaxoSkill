"""Behavioral contract for the framework-neutral ScienceWorld core."""

from __future__ import annotations

from typing import Any

import pytest

from scienceworld_env.core import CoreObservation, CoreState, CoreStep, ScienceWorldCore


class FakeSimulator:
    def __init__(self) -> None:
        self.load_calls: list[tuple[str, int, str, bool]] = []
        self.step_results: list[tuple[str, float, bool, dict[str, Any]]] = []
        self.reset_result: tuple[str, dict[str, Any]] = (
            "You are in the foundry.",
            {
                "taskDesc": "Task Description: Determine whether the metal pot conducts electricity.",
                "score": 0,
                "taskName": "task-2a-test-conductivity",
                "variationIdx": 412,
            },
        )
        self.closed = False
        self.close_calls = 0

    def load(
        self,
        task_name: str,
        variation_idx: int,
        simplification: str,
        generate_gold_path: bool,
    ) -> None:
        self.load_calls.append(
            (task_name, variation_idx, simplification, generate_gold_path)
        )

    def reset(self) -> tuple[str, dict[str, Any]]:
        return self.reset_result

    def step(self, action: str) -> tuple[str, float, bool, dict[str, Any]]:
        if not self.step_results:
            raise AssertionError(f"unexpected step: {action}")
        return self.step_results.pop(0)

    def close(self) -> None:
        self.closed = True
        self.close_calls += 1


def test_uninitialized_core_rejects_steps_and_unknown_tasks() -> None:
    simulator = FakeSimulator()
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    assert core.state() == CoreState(
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
    with pytest.raises(RuntimeError, match="must be reset before step"):
        core.step("look around")
    with pytest.raises(ValueError, match="unknown ScienceWorld task ID: 1888"):
        core.reset(1888)
    assert simulator.load_calls == []


def test_reset_selects_the_exact_frozen_task_and_normalizes_its_goal() -> None:
    simulator = FakeSimulator()
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    observation = core.reset(0)

    assert simulator.load_calls == [
        ("task-2a-test-conductivity", 412, "easy", False)
    ]
    assert observation == CoreObservation(
        task_id=0,
        text="You are in the foundry.",
        goal="Determine whether the metal pot conducts electricity.",
        score=0.0,
    )


def test_reset_accepts_the_task_name_canonicalized_by_scienceworld() -> None:
    simulator = FakeSimulator()
    setattr(simulator, "taskName", "test-conductivity")
    simulator.reset_result[1]["taskName"] = "test-conductivity"
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    observation = core.reset(0)

    assert observation.task_id == 0


def test_step_preserves_reward_and_tracks_current_best_and_terminal_scores() -> None:
    identity = {
        "taskName": "task-2a-test-conductivity",
        "variationIdx": 412,
    }
    simulator = FakeSimulator()
    simulator.step_results = [
        ("Progress.", 7.5, False, {**identity, "score": 40}),
        ("A setback.", -3.25, False, {**identity, "score": 20}),
        ("Solved.", 80.0, True, {**identity, "score": 100}),
    ]
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)
    reset_observation = core.reset(0)

    first = core.step("connect wire to battery")

    assert first == CoreStep(
        observation=CoreObservation(
            task_id=0,
            text="Progress.",
            goal=reset_observation.goal,
            score=40.0,
        ),
        reward=7.5,
        terminated=False,
    )
    assert core.state() == CoreState(
        task_id=0,
        goal=reset_observation.goal,
        current_score=40.0,
        best_score=40.0,
        progress=0.4,
        success=False,
        terminated=False,
        step_count=1,
        step_limit=49,
        closed=False,
    )

    second = core.step("disconnect wire")
    assert second.reward == -3.25
    assert second.observation.score == 20.0
    assert core.state().current_score == 20.0
    assert core.state().best_score == 40.0
    assert core.state().progress == 0.4

    final = core.step("place metal pot in blue box")
    assert final.terminated is True
    assert core.state().current_score == 100.0
    assert core.state().best_score == 100.0
    assert core.state().progress == 1.0
    assert core.state().success is True
    assert core.state().step_count == 3


def test_reset_rejects_an_empty_task_goal() -> None:
    simulator = FakeSimulator()
    simulator.reset_result = (
        "Initial room.",
        {
            "taskDesc": "Task Description:   ",
            "score": 0,
            "taskName": "task-2a-test-conductivity",
            "variationIdx": 412,
        },
    )
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    with pytest.raises(ValueError, match="ScienceWorld task 0 has an empty description"):
        core.reset(0)
    assert core.state().task_id is None


def test_reset_rejects_runtime_task_identity_drift() -> None:
    simulator = FakeSimulator()
    simulator.reset_result[1]["variationIdx"] = 999
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    with pytest.raises(
        ValueError,
        match=(
            "ScienceWorld runtime identity mismatch: expected "
            "task-2a-test-conductivity variation 412, got "
            "task-2a-test-conductivity variation 999"
        ),
    ):
        core.reset(0)
    assert core.state().task_id is None


def test_step_rejects_runtime_task_identity_drift_without_mutating_state() -> None:
    simulator = FakeSimulator()
    simulator.step_results = [
        (
            "Wrong task.",
            50.0,
            False,
            {
                "score": 50,
                "taskName": "task-3-find-animal",
                "variationIdx": 0,
            },
        )
    ]
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)
    core.reset(0)

    with pytest.raises(ValueError, match="ScienceWorld runtime identity mismatch"):
        core.step("look around")
    assert core.state().current_score == 0.0
    assert core.state().step_count == 0


def test_native_terminal_blocks_more_steps_and_negative_progress_clamps_to_zero() -> None:
    simulator = FakeSimulator()
    simulator.step_results = [
        (
            "Irreversible mistake.",
            -10.0,
            True,
            {
                "score": -10,
                "taskName": "task-2a-test-conductivity",
                "variationIdx": 412,
            },
        )
    ]
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)
    core.reset(0)

    transition = core.step("destroy metal pot")

    assert transition.terminated is True
    assert core.state().current_score == -10.0
    assert core.state().best_score == 0.0
    assert core.state().progress == 0.0
    with pytest.raises(RuntimeError, match="ScienceWorld episode has terminated"):
        core.step("look around")


def test_close_releases_the_simulator_once_and_rejects_further_use() -> None:
    simulator = FakeSimulator()
    core = ScienceWorldCore(scienceworld_factory=lambda: simulator)

    core.close()
    core.close()

    assert simulator.close_calls == 1
    assert core.state().closed is True
    with pytest.raises(RuntimeError, match="ScienceWorld core is closed"):
        core.reset(0)
    with pytest.raises(RuntimeError, match="ScienceWorld core is closed"):
        core.step("look around")
