"""Resolve immutable optimization data independently of optimization engine."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json

from taxoskill.config import EnvCfg, OptimizationCfg
from taxoskill.environment import Env
from taxoskill.optimization.environment import OptimizationEnvironmentAdapter
from taxoskill.optimization.candidate_pool import load_candidate_pool, restrict_candidate_pool
from taxoskill.optimization.partitioning.artifact import (
    PartitionArtifact,
    environment_description_hash,
    load_and_validate_partition,
    task_pool_hash,
    unique_pool_tasks,
)
from taxoskill.optimization.selection import select_task_splits
from taxoskill.optimization.tasks import OptimizationTaskPools, OptimizationTaskSplits, TaskKey


def _canonical_pools(pools: OptimizationTaskPools) -> OptimizationTaskPools:
    train = tuple(sorted(pools.train, key=lambda task: task.key))
    validation = tuple(sorted(pools.validation, key=lambda task: task.key))
    for label, tasks in (("train", train), ("validation", validation)):
        keys = [task.key for task in tasks]
        if len(set(keys)) != len(keys):
            raise ValueError(f"optimization {label} pool contains duplicate task keys")
    wrong_train_splits = sorted(
        {task.key.source_split for task in train} - {pools.train_source_split}
    )
    if wrong_train_splits:
        raise ValueError(
            f"optimization train pool has unexpected source splits: {wrong_train_splits}"
        )
    expected_validation_source = (
        pools.train_source_split
        if pools.shared_development_pool
        else pools.validation_source_split
    )
    wrong_validation_splits = sorted(
        {task.key.source_split for task in validation} - {expected_validation_source}
    )
    if wrong_validation_splits:
        raise ValueError(
            "optimization validation pool has unexpected source splits: "
            f"{wrong_validation_splits}"
        )
    if pools.shared_development_pool:
        if {task.key for task in train} != {task.key for task in validation}:
            raise ValueError("shared optimization pool train/validation records differ")
    elif {task.key for task in train} & {task.key for task in validation}:
        raise ValueError("separate train and validation pools overlap")
    return OptimizationTaskPools(
        train=train,
        validation=validation,
        shared_development_pool=pools.shared_development_pool,
        train_source_split=pools.train_source_split,
        validation_source_split=pools.validation_source_split,
    )


def resolve_optimization_data(
    *,
    optimization_cfg: OptimizationCfg,
    env_cfg: EnvCfg,
    seed: int,
    adapter: OptimizationEnvironmentAdapter,
    probe: Env,
    task_groups: list[str] | None,
    omission: float | None = None,
) -> tuple[OptimizationTaskSplits, PartitionArtifact | None]:
    normalized_groups = None if task_groups is None else sorted(task_groups)
    if normalized_groups is not None:
        if not normalized_groups:
            raise ValueError("optimization task-group selection must be non-empty")
        if len(set(normalized_groups)) != len(normalized_groups):
            raise ValueError("optimization task-group selection contains duplicates")

    pools = _canonical_pools(
        adapter.optimization_task_pools(probe, task_groups=normalized_groups)
    )

    full_pools = pools
    if optimization_cfg.candidate_pool_file is not None:
        manifest = load_candidate_pool(Path(optimization_cfg.candidate_pool_file),
                                       environment=env_cfg.name, seed=seed, omission=omission)
        pools = restrict_candidate_pool(full_pools, manifest)

    cluster_aware = (
        optimization_cfg.train_selection == "cluster"
        or optimization_cfg.validation_selection == "cluster"
    )
    partition = None
    assignments: dict[TaskKey, tuple[int, ...]] | None = None
    if cluster_aware:
        if optimization_cfg.partition_artifact is None:
            raise ValueError("cluster-aware optimization has no partition artifact")
        partition_path = Path(optimization_cfg.partition_artifact)
        saved_partition = PartitionArtifact.model_validate_json(partition_path.read_text())
        # Retain full-source partitions, while accepting independently discovered
        # candidate-pool taxonomies only against that exact validated candidate pool.
        partition_pools = (
            full_pools
            if saved_partition.task_pool_sha256 == task_pool_hash(unique_pool_tasks(full_pools))
            else pools
        )
        partition = load_and_validate_partition(
            partition_path,
            environment=env_cfg.name,
            task_groups=normalized_groups,
            pools=partition_pools,
            environment_asset_hashes=adapter.asset_hashes(probe),
            environment_description_sha256=environment_description_hash(
                adapter.environment_description(probe)
            ),
        )
        assignments = {item.key: tuple(item.cluster_ids) for item in partition.assignments}
        if len(assignments) != len(partition.assignments):
            raise ValueError("partition contains duplicate split-aware task keys")

    # Per-cluster skill training never performs a second selection. It validates the requested
    # cluster here, then slices the exact full-pool global-cluster split after selection below.
    selected_cluster: int | None = None
    if optimization_cfg.cluster_id is not None:
        selected_cluster = optimization_cfg.cluster_id
        if partition is None or assignments is None:
            raise ValueError("per-cluster training requires a loaded partition")
        if selected_cluster not in partition.cluster_sizes:
            raise ValueError(
                f"per-cluster training requested unknown cluster {selected_cluster}; "
                f"partition has {sorted(partition.cluster_sizes)}"
            )

    if optimization_cfg.candidate_pool_file is not None:
        if assignments is not None:
            allowed = {task.key for task in pools.train}
            assignments = {key: value for key, value in assignments.items() if key in allowed}

    splits = select_task_splits(
        pools,
        assignments=assignments,
        seed=seed,
        train_count=optimization_cfg.train_count,
        validation_count=optimization_cfg.validation_count,
        train_strategy=optimization_cfg.train_selection,
        validation_strategy=optimization_cfg.validation_selection,
    )

    if omission is not None and (optimization_cfg.candidate_pool_file is None or optimization_cfg.selection_lock_file is None):
        raise ValueError('Controlled-pool training requires a candidate pool and pinned selection lock')
    if optimization_cfg.selection_lock_file is not None:
        lock_path = Path(optimization_cfg.selection_lock_file)
        lock_bytes = lock_path.read_bytes()
        if hashlib.sha256(lock_bytes).hexdigest() != optimization_cfg.selection_lock_sha256:
            raise ValueError('selection lock file differs from its pinned SHA-256')
        lock = json.loads(lock_bytes)
        expected_scope = dict(environment=env_cfg.name, seed=seed,
                              omission=omission,
                              train_count=optimization_cfg.train_count,
                              validation_count=optimization_cfg.validation_count,
                              train_strategy=optimization_cfg.train_selection,
                              validation_strategy=optimization_cfg.validation_selection)
        if lock.get('schema_version') != 1 or any(lock.get(k) != v for k, v in expected_scope.items()):
            raise ValueError('selection lock scope/budgets/strategies differ from configuration')
        for source, digest in lock['source_hashes'].items():
            if hashlib.sha256(Path(source).read_bytes()).hexdigest() != digest:
                raise ValueError(f'selection lock source drift: {source}')
        pool_file = optimization_cfg.candidate_pool_file
        if pool_file is None or hashlib.sha256(Path(pool_file).read_bytes()).hexdigest() != lock['candidate_pool_sha256']:
            raise ValueError('selection lock candidate pool differs from configuration')
        partition_file = optimization_cfg.partition_artifact
        partition_sha = None if partition_file is None else hashlib.sha256(Path(partition_file).read_bytes()).hexdigest()
        if partition_sha != lock['partition_sha256']:
            raise ValueError('selection lock taxonomy differs from configuration')
        actual = {name: [task.key.canonical for task in getattr(splits, name)] for name in ('train', 'validation')}
        if actual != lock['task_ids']:
            raise ValueError('resolved training/validation IDs differ from locked selections')

    if selected_cluster is not None:
        assert assignments is not None
        train = tuple(
            task for task in splits.train
            if selected_cluster in assignments[task.key]
        )
        validation = tuple(
            task for task in splits.validation
            if selected_cluster in assignments[task.key]
        )
        if not train or not validation:
            raise RuntimeError(
                f"shared cluster selection gave cluster {selected_cluster} "
                f"{len(train)} train / {len(validation)} validation tasks"
            )
        splits = OptimizationTaskSplits(
            train=train,
            validation=validation,
            train_source_split=splits.train_source_split,
            validation_source_split=splits.validation_source_split,
        )
    return splits, partition
