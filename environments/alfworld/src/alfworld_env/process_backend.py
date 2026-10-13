"""Private spawn-based process supervisor for one ALFWorld simulator."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import multiprocessing
import traceback

from alfworld_env.core import BackendObservation


def _default_worker_backend_factory():
    from alfworld_env.runtime import TextAlfWorldBackend

    return TextAlfWorldBackend()


@dataclass(frozen=True, slots=True)
class _ResetRequest:
    gamefile: str


@dataclass(frozen=True, slots=True)
class _StepRequest:
    action: str


@dataclass(frozen=True, slots=True)
class _CloseRequest:
    pass


@dataclass(frozen=True, slots=True)
class _ObservationResponse:
    observation: BackendObservation


@dataclass(frozen=True, slots=True)
class _ClosedResponse:
    pass


@dataclass(frozen=True, slots=True)
class _ErrorResponse:
    operation: str
    exception_type: str
    message: str
    remote_traceback: str


class ProcessBackendError(RuntimeError):
    """Structured failure raised in the parent for a remote worker exception."""

    def __init__(
        self,
        *,
        operation: str,
        exception_type: str,
        message: str,
        remote_traceback: str,
    ) -> None:
        super().__init__(
            f"ALFWorld worker {operation} failed with {exception_type}: {message}\n"
            f"{remote_traceback}"
        )
        self.operation = operation
        self.exception_type = exception_type
        self.remote_message = message
        self.remote_traceback = remote_traceback


def _worker_main(connection, backend_factory) -> None:
    backend = None
    try:
        while True:
            try:
                request = connection.recv()
            except EOFError:
                return
            if isinstance(request, _CloseRequest):
                return
            if isinstance(request, _ResetRequest):
                operation = "reset"
            elif isinstance(request, _StepRequest):
                operation = "step"
            else:
                connection.send(
                    _ErrorResponse(
                        operation="protocol",
                        exception_type="TypeError",
                        message=f"unsupported worker request: {request!r}",
                        remote_traceback="",
                    )
                )
                continue
            try:
                if operation == "reset":
                    if backend is None:
                        backend = backend_factory()
                    observation = backend.reset(request.gamefile)
                else:
                    if backend is None:
                        raise RuntimeError(
                            "ALFWorld worker must be reset before step"
                        )
                    observation = backend.step(request.action)
            except Exception as error:
                connection.send(
                    _ErrorResponse(
                        operation=operation,
                        exception_type=type(error).__name__,
                        message=str(error),
                        remote_traceback=traceback.format_exc(),
                    )
                )
            else:
                connection.send(_ObservationResponse(observation))
    finally:
        try:
            if backend is not None:
                backend.close()
        finally:
            try:
                connection.send(_ClosedResponse())
            except (BrokenPipeError, OSError):
                pass
            connection.close()


_WorkerBackendFactory = Callable[[], object]


class ProcessAlfWorldBackend:
    """Parent-side supervisor owning exactly one spawned ALFWorld worker."""

    def __init__(
        self,
        backend_factory: _WorkerBackendFactory = _default_worker_backend_factory,
        *,
        close_timeout_seconds: float = 5.0,
    ) -> None:
        if close_timeout_seconds <= 0:
            raise ValueError("close_timeout_seconds must be positive")
        context = multiprocessing.get_context("spawn")
        parent_connection, child_connection = context.Pipe(duplex=True)
        self._process = context.Process(
            target=_worker_main,
            args=(child_connection, backend_factory),
            daemon=True,
        )
        self._process.start()
        child_connection.close()
        self._connection = parent_connection
        self._close_timeout_seconds = close_timeout_seconds
        self._closed = False

    def reset(self, gamefile: str) -> BackendObservation:
        return self._request(_ResetRequest(gamefile), operation="reset")

    def step(self, action: str) -> BackendObservation:
        return self._request(_StepRequest(action), operation="step")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._process.is_alive():
                try:
                    self._connection.send(_CloseRequest())
                except (BrokenPipeError, EOFError, OSError):
                    pass
                else:
                    if self._connection.poll(self._close_timeout_seconds):
                        try:
                            self._connection.recv()
                        except (EOFError, OSError):
                            pass
                self._process.join(timeout=self._close_timeout_seconds)
            else:
                self._process.join(timeout=0)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=self._close_timeout_seconds)
            if self._process.is_alive():
                self._process.kill()
                self._process.join(timeout=self._close_timeout_seconds)
            if self._process.is_alive():
                raise RuntimeError("ALFWorld worker did not stop during close")
        finally:
            self._connection.close()

    def _request(self, request, *, operation: str) -> BackendObservation:
        if self._closed:
            raise RuntimeError("ALFWorld process backend is closed")
        try:
            self._connection.send(request)
            response = self._connection.recv()
        except (BrokenPipeError, EOFError, OSError) as error:
            self._process.join(timeout=0.1)
            raise RuntimeError(
                f"ALFWorld worker exited unexpectedly during {operation} "
                f"(exit code {self._process.exitcode})"
            ) from error
        if isinstance(response, _ErrorResponse):
            raise ProcessBackendError(
                operation=response.operation,
                exception_type=response.exception_type,
                message=response.message,
                remote_traceback=response.remote_traceback,
            )
        if not isinstance(response, _ObservationResponse):
            raise RuntimeError(
                f"ALFWorld worker sent an invalid {operation} response: {response!r}"
            )
        return response.observation
