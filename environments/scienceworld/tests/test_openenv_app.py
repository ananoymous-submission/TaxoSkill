"""Structural contract for the ScienceWorld OpenEnv application."""

from __future__ import annotations

from scienceworld_env.server.app import create_scienceworld_app
from scienceworld_env.server.environment import ScienceWorldEnvironment


def test_app_exposes_openenv_routes_with_48_session_capacity() -> None:
    app = create_scienceworld_app(max_concurrent_envs=48)
    paths = {route.path for route in app.routes}

    assert {"/health", "/metadata", "/schema", "/tools", "/ws"} <= paths
    assert ScienceWorldEnvironment.SUPPORTS_CONCURRENT_SESSIONS is True
