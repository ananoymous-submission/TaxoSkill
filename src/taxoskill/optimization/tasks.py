"""Engine-neutral identities and records for optimization task data."""

from __future__ import annotations

from dataclasses import dataclass
@dataclass(frozen=True, order=True)
class TaskKey:
    """A task identity scoped by its authoritative environment split."""

    source_split: str
    task_idx: int

    def __post_init__(self) -> None:
        if not self.source_split:
            raise ValueError("task source_split must be non-empty")
        if self.task_idx < 0:
            raise ValueError("task_idx must be non-negative")

    @property
    def canonical(self) -> str:
        return f"{self.source_split}:{self.task_idx}"


@dataclass(frozen=True)
class OptimizationTask:
    key: TaskKey
    task_type: str
    instruction: str

    def __post_init__(self) -> None:
        if not self.task_type:
            raise ValueError("optimization task_type must be non-empty")
        if not self.instruction.strip():
            raise ValueError("optimization task instruction must be non-empty")

    @property
    def task_idx(self) -> int:
        return self.key.task_idx

    @property
    def source_split(self) -> str:
        return self.key.source_split


@dataclass(frozen=True)
class OptimizationTaskPools:
    train: tuple[OptimizationTask, ...]
    validation: tuple[OptimizationTask, ...]
    shared_development_pool: bool
    train_source_split: str
    validation_source_split: str


@dataclass(frozen=True)
class SelectedTask:
    key: TaskKey
    task_type: str

@dataclass(frozen=True)
class OptimizationTaskSplits:
    train: tuple[SelectedTask, ...]
    validation: tuple[SelectedTask, ...]
    train_source_split: str
    validation_source_split: str
