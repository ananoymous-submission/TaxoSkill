"""Real WebSocket lifecycle contract for the ALFWorld OpenEnv server."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from alfworld_env.core import CoreObservation, CoreState, CoreStep
from alfworld_env.server.app import create_alfworld_app
from alfworld_env.server.environment import AlfWorldEnvironment


class RecordingCore:
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
            goal="Inspect the alarmclock.",
            closed=False,
        )
        return CoreObservation(
            task_id=task_id,
            text="Initial.",
            goal="Inspect the alarmclock.",
            admissible_actions=("look",),
        )

    def step(self, action: str) -> CoreStep:
        self.step_calls.append(action)
        self._state = replace(self._state, step_count=1)
        return CoreStep(
            observation=CoreObservation(
                task_id=self._state.task_id or 0,
                text="Stepped.",
                goal="Inspect the alarmclock.",
                admissible_actions=("look",),
            ),
            reward=0.0,
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

    class TestEnvironment(AlfWorldEnvironment):
        def __init__(self) -> None:
            core = RecordingCore()
            cores.append(core)
            super().__init__(core_factory=lambda: core)  # type: ignore[arg-type]

    app = create_alfworld_app(
        max_concurrent_envs=1,
        environment_factory=TestEnvironment,
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {"type": "reset", "data": {"task_id": 191, "episode_id": "episode-191"}}
            )
            reset_response = websocket.receive_json()
            websocket.send_json({"type": "step", "data": {"command": "look"}})
            step_response = websocket.receive_json()
            websocket.send_json({"type": "state"})
            state_response = websocket.receive_json()

        assert reset_response["type"] == "observation"
        assert reset_response["data"]["observation"]["task_id"] == 191
        assert step_response["data"]["observation"]["text"] == "Stepped."
        assert state_response["type"] == "state"
        assert state_response["data"]["episode_id"] == "episode-191"

    assert len(cores) == 1
    assert cores[0].reset_calls == [191]
    assert cores[0].step_calls == ["look"]
    assert cores[0].close_calls == 1
