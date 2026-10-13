"""Common task-selection contracts and strict validation."""

from __future__ import annotations

from typing import Protocol, Sequence

from taxoskill.optimization.tasks import OptimizationTask


class TaskSelector(Protocol):
    """Select an exact task subset from an already-visible optimization pool."""

    def select(
        self,
        tasks: Sequence[OptimizationTask],
        count: int,
        *,
        seed: int,
        namespace: str,
    ) -> list[OptimizationTask]: ...


def validate_selection_request(
    tasks: Sequence[OptimizationTask], count: int
) -> None:
    if count < 1:
        raise ValueError("task selection count must be >= 1")
    if count > len(tasks):
        raise ValueError(f"cannot select {count} tasks from a pool of {len(tasks)}")
    task_keys = [task.key for task in tasks]
    if len(set(task_keys)) != len(task_keys):
        raise ValueError("task selection pool contains duplicate task keys")
