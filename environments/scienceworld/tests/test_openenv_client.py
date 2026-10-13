"""Typed-client contract for the ScienceWorld OpenEnv runtime."""

from __future__ import annotations

import asyncio

import pytest

import scienceworld_env.client as client_module
from scienceworld_env.client import ScienceWorldClient
from scienceworld_env.models import ScienceWorldAction, ScienceWorldObservation, ScienceWorldState


def test_client_serializes_actions_and_parses_typed_results_and_state() -> None:
    client = ScienceWorldClient(base_url="http://localhost:8000")
    action = ScienceWorldAction(command="look around")

    assert client._step_payload(action) == {
        "metadata": {},
        "command": "look around",
    }

    result = client._parse_result(
        {
            "observation": {
                "metadata": {},
                "task_id": 17,
                "text": "Task complete.",
                "goal": "Determine conductivity.",
                "score": 100.0,
                "best_score": 100.0,
                "progress": 1.0,
                "success": True,
                "terminated": True,
                "truncated": False,
            },
            "reward": 100.0,
            # The typed client derives completion from the explicit terminal flags.
            "done": False,
            "metadata": {"server": "scienceworld"},
        }
    )

    assert result.observation == ScienceWorldObservation(
        task_id=17,
        text="Task complete.",
        goal="Determine conductivity.",
        score=100.0,
        best_score=100.0,
        progress=1.0,
        success=True,
        terminated=True,
        truncated=False,
        reward=100.0,
        done=True,
        metadata={"server": "scienceworld"},
    )
    assert result.reward == 100.0
    assert result.done is True
    assert result.metadata == {"server": "scienceworld"}

    assert client._parse_state(
        {
            "episode_id": "episode-17",
            "step_count": 1,
            "task_id": 17,
            "goal": "Determine conductivity.",
            "current_score": 100.0,
            "best_score": 100.0,
            "progress": 1.0,
            "success": True,
            "terminated": True,
            "truncated": False,
            "step_limit": 49,
            "closed": False,
        }
    ) == ScienceWorldState(
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


def test_client_adds_bearer_token_to_private_space_websocket(monkeypatch) -> None:
    calls = []

    async def fake_connect(uri, **kwargs):
        calls.append((uri, kwargs))
        return object()

    monkeypatch.setattr(client_module, "_authenticated_ws_connect", fake_connect)
    client = ScienceWorldClient(
        base_url="https://private-space.hf.space",
        bearer_token="x",
    )

    asyncio.run(client._connect_async())

    assert calls[0][1]["bearer_token"] == "x"


def test_client_rejects_bearer_token_over_plaintext_transport() -> None:
    with pytest.raises(ValueError, match="requires an HTTPS or WSS endpoint"):
        ScienceWorldClient(
            base_url="http://private-space.hf.space",
            bearer_token="x",
        )


def test_authenticated_websocket_rejects_redirects(monkeypatch) -> None:
    monkeypatch.setattr(
        client_module.ws_connect,
        "process_redirect",
        lambda self, error: "wss://other.example/ws",
    )
    connection = client_module._AuthenticatedConnect("wss://private-space.hf.space/ws")

    result = connection.process_redirect(Exception("redirect"))

    assert isinstance(result, client_module.SecurityError)
