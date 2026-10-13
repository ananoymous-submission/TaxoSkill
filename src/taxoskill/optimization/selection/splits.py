"""Engine-neutral total-budget train/validation selection with sealed test handling."""

from __future__ import annotations

from typing import Literal, Mapping

from taxoskill.optimization.selection.base import TaskSelector
from taxoskill.optimization.selection.cluster import (
    ClusterTaskSelector,
    select_joint_cluster_splits,
)
from taxoskill.optimization.selection.random import RandomTaskSelector
from taxoskill.optimization.tasks import (
    OptimizationTask,
    OptimizationTaskPools,
    OptimizationTaskSplits,
    SelectedTask,
    TaskKey,
)


SelectionStrategy = Literal["random", "cluster"]


def _selector(
    strategy: SelectionStrategy,
    assignments: Mapping[TaskKey, tuple[int, ...]] | None,
) -> TaskSelector:
    if strategy == "random":
        return RandomTaskSelector()
    if strategy == "cluster":
        if assignments is None:
            raise ValueError("cluster task selection requires cluster assignments")
        return ClusterTaskSelector(assignments)
    raise ValueError(f"unsupported task selection strategy {strategy!r}")


def _select(
    tasks: tuple[OptimizationTask, ...] | list[OptimizationTask],
    count: int,
    strategy: SelectionStrategy,
    assignments: Mapping[TaskKey, tuple[int, ...]] | None,
    *,
    seed: int,
    namespace: str,
) -> list[OptimizationTask]:
    return _selector(strategy, assignments).select(
        tasks,
        count,
        seed=seed,
        namespace=namespace,
    )


def select_task_splits(
    pools: OptimizationTaskPools,
    *,
    assignments: Mapping[TaskKey, tuple[int, ...]] | None,
    seed: int,
    train_count: int,
    validation_count: int,
    train_strategy: SelectionStrategy,
    validation_strategy: SelectionStrategy,
) -> OptimizationTaskSplits:
    if pools.shared_development_pool:
        if (
            assignments is not None
            and train_strategy == "cluster"
            and validation_strategy == "cluster"
        ):
            # One joint deterministic selection is the sole cluster-aware train/validation path.
            # Global-cluster consumes this complete split; per-cluster slices the same split later.
            train, validation = select_joint_cluster_splits(
                pools.train,
                assignments,
                train_count=train_count,
                validation_count=validation_count,
                seed=seed,
            )
        else:
            # Non-cluster and mixed policies retain the general path.
            validation = _select(
                pools.validation,
                validation_count,
                validation_strategy,
                assignments,
                seed=seed,
                namespace="validation",
            )
            validation_keys = {task.key for task in validation}
            remaining = tuple(
                task for task in pools.train if task.key not in validation_keys
            )
            train = _select(
                remaining,
                train_count,
                train_strategy,
                assignments,
                seed=seed,
                namespace="training",
            )
    else:
        train = _select(
            pools.train,
            train_count,
            train_strategy,
            assignments,
            seed=seed,
            namespace="training",
        )
        validation = _select(
            pools.validation,
            validation_count,
            validation_strategy,
            assignments,
            seed=seed,
            namespace="validation",
        )

    train_keys = {task.key for task in train}
    validation_keys = {task.key for task in validation}
    if len(train_keys) != train_count:
        raise RuntimeError("training selector returned the wrong total task count")
    if len(validation_keys) != validation_count:
        raise RuntimeError("validation selector returned the wrong total task count")
    if train_keys & validation_keys:
        raise ValueError("training and validation selections overlap")
    def selected_task(task: OptimizationTask) -> SelectedTask:
        if assignments is not None:
            try:
                assignments[task.key]
            except KeyError as error:
                raise ValueError(
                    f"selected task {task.key.canonical} has no partition assignment"
                ) from error
        return SelectedTask(
            key=task.key,
            task_type=task.task_type,
        )

    return OptimizationTaskSplits(
        train=tuple(selected_task(task) for task in train),
        validation=tuple(selected_task(task) for task in validation),
        train_source_split=pools.train_source_split,
        validation_source_split=pools.validation_source_split,
    )
