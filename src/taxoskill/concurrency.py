"""Concurrency primitives with explicit failure behavior."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Self


class FailFastThreadPoolExecutor(ThreadPoolExecutor):
    """Cancel queued work instead of draining it after a worker failure."""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_value, traceback
        failed = exc_type is not None
        self.shutdown(wait=not failed, cancel_futures=failed)
