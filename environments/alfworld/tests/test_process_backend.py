"""Contract tests for the spawn-based ALFWorld process backend."""

from __future__ import annotations

from functools import partial
import multiprocessing
import os
import time

import pytest

from alfworld_env.core import BackendObservation
from alfworld_env.process_backend import ProcessAlfWorldBackend, ProcessBackendError


_FIXTURE_OBSERVATION = BackendObservation(
    text="reset:fixture",
    admissible_actions=("look",),
    runtime_task_type="look_at_obj_in_light-fixture/trial",
    reward=0.0,
    terminated=False,
)


class ScriptedWorkerBackend:
    """Top-level picklable fake simulator constructed inside the worker."""

    def __init__(self) -> None:
        self._gamefile: str | None = None

    def reset(self, gamefile: str) -> BackendObservation:
        self._gamefile = gamefile
        return BackendObservation(
            text=f"reset:{gamefile}",
            admissible_actions=("look", "inventory"),
            runtime_task_type="look_at_obj_in_light-fixture/trial",
            reward=0.0,
            terminated=False,
        )

    def step(self, action: str) -> BackendObservation:
        if self._gamefile is None:
            raise RuntimeError("scripted backend stepped before reset")
        return BackendObservation(
            text=f"step:{action}",
            admissible_actions=("look",),
            runtime_task_type="look_at_obj_in_light-fixture/trial",
            reward=1.0,
            terminated=True,
        )

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _no_worker_survives_any_test():
    yield
    stragglers = multiprocessing.active_children()
    for child in stragglers:
        child.terminate()
        child.join(timeout=5)
    assert stragglers == []


def test_process_backend_round_trips_reset_and_step_through_one_worker() -> None:
    backend = ProcessAlfWorldBackend(backend_factory=ScriptedWorkerBackend)
    try:
        observation = backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")

        assert observation == BackendObservation(
            text="reset:json_2.1.1/train/fixture/trial/game.tw-pddl",
            admissible_actions=("look", "inventory"),
            runtime_task_type="look_at_obj_in_light-fixture/trial",
            reward=0.0,
            terminated=False,
        )

        transition = backend.step("look")

        assert transition == BackendObservation(
            text="step:look",
            admissible_actions=("look",),
            runtime_task_type="look_at_obj_in_light-fixture/trial",
            reward=1.0,
            terminated=True,
        )
    finally:
        backend.close()


class RecordingWorkerBackend:
    """Append every lifecycle call to a shared file across the process boundary."""

    def __init__(self, record_path: str) -> None:
        self._record_path = record_path

    def _record(self, line: str) -> None:
        with open(self._record_path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def reset(self, gamefile: str) -> BackendObservation:
        self._record(f"reset:{gamefile}")
        return _FIXTURE_OBSERVATION

    def step(self, action: str) -> BackendObservation:
        self._record(f"step:{action}")
        return _FIXTURE_OBSERVATION

    def close(self) -> None:
        self._record("close")


class CrashingStepBackend(ScriptedWorkerBackend):
    def step(self, action: str) -> BackendObservation:
        raise ValueError(f"engine exploded on {action!r}")


class ExitingStepBackend(ScriptedWorkerBackend):
    def step(self, action: str) -> BackendObservation:
        os._exit(3)


class HangingCloseBackend(ScriptedWorkerBackend):
    def close(self) -> None:
        time.sleep(60.0)


def test_close_is_idempotent_and_closes_the_worker_backend_exactly_once(
    tmp_path,
) -> None:
    record_path = tmp_path / "calls.log"
    backend = ProcessAlfWorldBackend(
        backend_factory=partial(RecordingWorkerBackend, str(record_path))
    )
    backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")

    backend.close()
    backend.close()

    assert backend._process.is_alive() is False
    assert backend._process.exitcode == 0
    lines = record_path.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "reset:json_2.1.1/train/fixture/trial/game.tw-pddl",
        "close",
    ]


def test_close_before_reset_still_releases_the_worker() -> None:
    backend = ProcessAlfWorldBackend(backend_factory=ScriptedWorkerBackend)

    backend.close()

    assert backend._process.is_alive() is False
    assert backend._process.exitcode == 0


def test_calls_after_close_raise_a_clear_runtime_error() -> None:
    backend = ProcessAlfWorldBackend(backend_factory=ScriptedWorkerBackend)
    backend.close()

    with pytest.raises(RuntimeError, match="ALFWorld process backend is closed"):
        backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")
    with pytest.raises(RuntimeError, match="ALFWorld process backend is closed"):
        backend.step("look")


def test_worker_exception_propagates_operation_type_message_and_traceback() -> None:
    backend = ProcessAlfWorldBackend(backend_factory=CrashingStepBackend)
    try:
        backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")

        with pytest.raises(ProcessBackendError) as excinfo:
            backend.step("look")

        error = excinfo.value
        assert error.operation == "step"
        assert error.exception_type == "ValueError"
        assert error.remote_message == "engine exploded on 'look'"
        assert "ValueError: engine exploded on 'look'" in error.remote_traceback
        assert "Traceback" in error.remote_traceback
    finally:
        backend.close()


def test_unexpected_worker_exit_raises_instead_of_hanging() -> None:
    backend = ProcessAlfWorldBackend(backend_factory=ExitingStepBackend)
    try:
        backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")

        with pytest.raises(RuntimeError, match="exited unexpectedly during step"):
            backend.step("look")
    finally:
        backend.close()

    assert backend._process.is_alive() is False


def test_close_terminates_the_worker_when_graceful_join_times_out() -> None:
    backend = ProcessAlfWorldBackend(
        backend_factory=HangingCloseBackend,
        close_timeout_seconds=0.5,
    )
    backend.reset("json_2.1.1/train/fixture/trial/game.tw-pddl")

    started = time.monotonic()
    backend.close()
    elapsed = time.monotonic() - started

    assert backend._process.is_alive() is False
    assert elapsed < 10.0
