"""Structural contract for the ALFWorld OpenEnv application."""

from __future__ import annotations

from alfworld_env.server.app import create_alfworld_app


def test_app_exposes_openenv_routes_with_explicit_rollout_capacity() -> None:
    app = create_alfworld_app(max_concurrent_envs=1)
    paths = {route.path for route in app.routes}

    assert {"/health", "/metadata", "/schema", "/tools", "/ws"} <= paths
    create_alfworld_app(max_concurrent_envs=24)
