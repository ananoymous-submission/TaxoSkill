"""Real WebSocket lifecycle tests for the ScienceWorld OpenEnv server."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from scienceworld_env.core import CoreObservation, CoreState, CoreStep
from scienceworld_env.server.app import create_scienceworld_app
from scienceworld_env.server.environment import ScienceWorldEnvironment


class RecordingCore:
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
        self._state = replace(
            self._state,
            task_id=task_id,
            goal="Test goal.",
            closed=False,
        )
        return CoreObservation(task_id=task_id, text="Initial.", goal="Test goal.", score=0.0)

    def step(self, action: str) -> CoreStep:
        self.step_calls.append(action)
        self._state = replace(
            self._state,
            current_score=10.0,
            best_score=10.0,
            progress=0.1,
            step_count=1,
        )
        return CoreStep(
            observation=CoreObservation(
                task_id=self._state.task_id or 0,
                text="Stepped.",
                goal="Test goal.",
                score=10.0,
            ),
            reward=10.0,
            terminated=False,
        )

    def state(self) -> CoreState:
        return self._state

    def close(self) -> None:
        if not self._state.closed:
            self.close_calls += 1
            self._state = replace(self._state, closed=True)


def test_websocket_owns_one_core_and_disconnect_closes_it() -> None:
    cores: list[RecordingCore] = []

    class TestEnvironment(ScienceWorldEnvironment):
        def __init__(self) -> None:
            core = RecordingCore()
            cores.append(core)
            super().__init__(core_factory=lambda: core)  # type: ignore[arg-type]

    app = create_scienceworld_app(
        max_concurrent_envs=1,
        environment_factory=TestEnvironment,
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {"type": "reset", "data": {"task_id": 17, "episode_id": "episode-17"}}
            )
            reset_response = websocket.receive_json()
            websocket.send_json({"type": "step", "data": {"command": "look around"}})
            step_response = websocket.receive_json()
            websocket.send_json({"type": "state"})
            state_response = websocket.receive_json()

        assert reset_response["type"] == "observation"
        assert reset_response["data"]["observation"]["task_id"] == 17
        assert step_response["data"]["observation"]["text"] == "Stepped."
        assert state_response["type"] == "state"
        assert state_response["data"]["episode_id"] == "episode-17"

    assert len(cores) == 1
    assert cores[0].reset_calls == [17]
    assert cores[0].step_calls == ["look around"]
    assert cores[0].close_calls == 1
