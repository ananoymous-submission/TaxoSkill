"""FastAPI and WebSocket entrypoint for the ALFWorld OpenEnv environment."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import FastAPI
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.interfaces import Environment

from alfworld_env.models import AlfWorldAction, AlfWorldObservation, native_tool_specs
from alfworld_env.server.environment import AlfWorldEnvironment


def _configured_capacity() -> int:
    raw = os.getenv("MAX_CONCURRENT_ENVS", "1")
    try:
        capacity = int(raw)
    except ValueError as error:
        raise ValueError(f"MAX_CONCURRENT_ENVS must be an integer, got {raw!r}") from error
    if capacity < 1:
        raise ValueError("MAX_CONCURRENT_ENVS must be at least 1")
    return capacity


def _configured_default_task_id() -> int | None:
    raw = os.getenv("DEFAULT_TASK_ID")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError(f"DEFAULT_TASK_ID must be an integer, got {raw!r}") from error


def _configured_environment_class(
    default_task_id: int | None,
) -> type[AlfWorldEnvironment]:
    if default_task_id is None:
        return AlfWorldEnvironment

    class ConfiguredAlfWorldEnvironment(AlfWorldEnvironment):
        def __init__(self) -> None:
            super().__init__(default_task_id=default_task_id)

    ConfiguredAlfWorldEnvironment.__name__ = "AlfWorldEnvironment"
    return ConfiguredAlfWorldEnvironment


def create_alfworld_app(
    max_concurrent_envs: int | None = None,
    environment_factory: Callable[[], Environment] | None = None,
) -> FastAPI:
    """Create the pinned OpenEnv server without constructing an episode eagerly."""

    capacity = _configured_capacity() if max_concurrent_envs is None else max_concurrent_envs
    factory = environment_factory or _configured_environment_class(
        _configured_default_task_id()
    )
    app = create_app(
        factory,
        AlfWorldAction,
        AlfWorldObservation,
        env_name="alfworld_env",
        max_concurrent_envs=capacity,
    )
    app.add_api_route("/tools", native_tool_specs, methods=["GET"])
    return app


app = create_alfworld_app()


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the standalone OpenEnv server."""

    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
