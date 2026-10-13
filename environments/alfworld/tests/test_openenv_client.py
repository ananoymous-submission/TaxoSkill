"""Typed-client contract for the ALFWorld OpenEnv runtime."""

from __future__ import annotations

from openenv.core.client_types import StepResult

from alfworld_env.client import AlfWorldClient
from alfworld_env.models import AlfWorldAction, AlfWorldObservation, AlfWorldState


def test_client_serializes_actions_and_parses_typed_results_and_state() -> None:
    client = AlfWorldClient(base_url="http://localhost:8000")
    action = AlfWorldAction(command="look")

    assert client._step_payload(action) == {"metadata": {}, "command": "look"}

    result = client._parse_result(
        {
            "observation": {
                "metadata": {},
                "task_id": 57,
                "text": "Done.",
                "goal": "Put the apple on the table.",
                "admissible_actions": ["look"],
                "success": True,
                "terminated": True,
                "truncated": False,
            },
            "reward": 1.0,
            "done": True,
        }
    )

    assert result == StepResult(
        observation=AlfWorldObservation(
            task_id=57,
            text="Done.",
            goal="Put the apple on the table.",
            admissible_actions=["look"],
            success=True,
            terminated=True,
            truncated=False,
            reward=1.0,
            done=True,
        ),
        reward=1.0,
        done=True,
        metadata={},
    )
    assert client._parse_state(
        {
            "episode_id": "episode-57",
            "step_count": 1,
            "task_id": 57,
            "goal": "Put the apple on the table.",
            "reward": 1.0,
            "success": True,
            "terminated": True,
            "truncated": False,
            "step_limit": 50,
            "closed": False,
        }
    ) == AlfWorldState(
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
