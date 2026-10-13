"""Frozen task-partition artifact: the contract cluster-aware selection and sampling consume.

A partition maps every task in an environment's optimization pool to a cluster. How the clusters
are produced is not this module's concern; it only pins the artifact to the environment, the task
pool and the environment description it was built for, and validates its internal consistency.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from taxoskill.optimization.partitioning.methods.base import MethodResult
from taxoskill.optimization.tasks import OptimizationTask, OptimizationTaskPools, TaskKey


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def instruction_hash(instruction: str) -> str:
    return sha256_bytes(instruction.encode("utf-8"))


def environment_description_hash(description: str) -> str:
    stripped = description.strip()
    if not stripped:
        raise ValueError("environment description must not be empty")
    return sha256_bytes(stripped.encode("utf-8"))


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskArchetype(StrictModel):
    task_type_id: str
    name: str
    definition: str


class TaskAssignment(StrictModel):
    task_idx: int
    source_split: str
    instruction_sha256: str
    cluster_ids: list[int]  # sorted, distinct cluster ids of the task
    task_archetype_ids: list[str]  # parallel to cluster_ids
    rationale: str

    @property
    def key(self) -> TaskKey:
        return TaskKey(self.source_split, self.task_idx)


class PartitionArtifact(StrictModel):
    schema_version: Literal[10]
    partition_id: str
    method: str
    environment: str
    seed: int  # partition-construction provenance; independent of optimization seeds
    task_groups: list[str] | None
    shared_development_pool: bool
    train_source_split: str
    validation_source_split: str
    environment_asset_hashes: dict[str, str]
    environment_description_sha256: str
    task_pool_sha256: str
    task_types: list[TaskArchetype]
    assignments: list[TaskAssignment]
    cluster_sizes: dict[int, int]  # number of tasks in each cluster
    embedding_fingerprint: str | None = None
    embedding_array_sha256: str | None = None
    embedding_model: str | None = None


class InstructionPool(Protocol):
    @property
    def env(self) -> str: ...

    @property
    def task_ids(self) -> list[str]: ...

    @property
    def instructions(self) -> list[str]: ...

    @property
    def initial_observations(self) -> list[str]: ...

    @property
    def task_types(self) -> list[str]: ...


def unique_pool_tasks(pools: OptimizationTaskPools) -> list[OptimizationTask]:
    tasks_by_key: dict[TaskKey, OptimizationTask] = {}
    for task in [*pools.train, *pools.validation]:
        previous = tasks_by_key.get(task.key)
        if previous is not None and previous != task:
            raise ValueError(
                f"task {task.key.canonical} has conflicting optimization-pool records"
            )
        tasks_by_key[task.key] = task
    if not tasks_by_key:
        raise ValueError("optimization task pool is empty")
    return [tasks_by_key[key] for key in sorted(tasks_by_key)]


def task_pool_hash(tasks: list[OptimizationTask]) -> str:
    """Identity of the task pool. Hashes exactly the fields ``assignment_pool_hash`` hashes, so a
    partition's ``task_pool_sha256`` can be checked either against live tasks or, without loading
    instructions, against the artifact's own assignments. (The initial observation is pinned by
    the environment asset hashes, not here.)"""
    payload = [
        {
            "task_idx": task.task_idx,
            "source_split": task.source_split,
            "instruction_sha256": instruction_hash(task.instruction),
        }
        for task in sorted(tasks, key=lambda item: item.key)
    ]
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def build_method_partition(
    *,
    pool: InstructionPool,
    optimizer_task_indices: list[int],
    result: MethodResult,
    environment_asset_hashes: dict[str, str],
    environment_description: str,
    train_source_split: str,
    validation_source_split: str,
    shared_development_pool: bool,
    embedding_fingerprint: str,
    embedding_array_sha256: str,
    embedding_model: str,
) -> PartitionArtifact:
    """Build an optimizer-facing partition from a complete clustering result."""
    if not result.deployable or result.n_noise:
        raise ValueError("cannot export a clustering with noise as a complete partition")
    if len(result.labels) != len(pool.task_ids):
        raise ValueError("clustering labels do not cover the task pool")
    if len(optimizer_task_indices) != len(pool.task_ids):
        raise ValueError("optimizer task indices do not cover the task pool")
    if len(set(optimizer_task_indices)) != len(optimizer_task_indices):
        raise ValueError("optimizer task indices must be unique")
    if any(index < 0 for index in optimizer_task_indices):
        raise ValueError("optimizer task indices must be non-negative")

    archetypes = [
        TaskArchetype(
            task_type_id=f"type-{cluster_id:04d}",
            name=f"cluster_{cluster_id}",
            definition=f"{result.method} cluster {cluster_id}",
        )
        for cluster_id in range(result.n_clusters)
    ]
    assignments = [
        TaskAssignment(
            task_idx=task_idx,
            source_split=train_source_split,
            instruction_sha256=instruction_hash(instruction),
            cluster_ids=[label],
            task_archetype_ids=[f"type-{label:04d}"],
            rationale=f"{result.method} with label-free parameters {result.selected_params}",
        )
        for task_idx, instruction, label in sorted(
            zip(optimizer_task_indices, pool.instructions, result.labels, strict=True),
            key=lambda item: TaskKey(train_source_split, item[0]),
        )
    ]
    pool_sha = assignment_pool_hash(assignments)
    partition_id = sha256_bytes(json.dumps({
        "environment": pool.env,
        "method": result.method,
        "seed": result.seed,
        "pool": pool_sha,
        "params": result.selected_params,
        "labels": result.labels,
        "embedding_fingerprint": embedding_fingerprint,
        "embedding_array_sha256": embedding_array_sha256,
        "embedding_model": embedding_model,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8"))[:20]
    return PartitionArtifact(
        schema_version=10,
        partition_id=partition_id,
        method=f"{result.method}: label-free parameter selection",
        environment=pool.env,
        seed=result.seed,
        task_groups=None,
        shared_development_pool=shared_development_pool,
        train_source_split=train_source_split,
        validation_source_split=validation_source_split,
        environment_asset_hashes=environment_asset_hashes,
        environment_description_sha256=environment_description_hash(environment_description),
        task_pool_sha256=pool_sha,
        task_types=archetypes,
        assignments=assignments,
        cluster_sizes=result.cluster_sizes,
        embedding_fingerprint=embedding_fingerprint,
        embedding_array_sha256=embedding_array_sha256,
        embedding_model=embedding_model,
    )


def assignment_pool_hash(assignments: list[TaskAssignment]) -> str:
    payload = [
        {
            "task_idx": item.task_idx,
            "source_split": item.source_split,
            "instruction_sha256": item.instruction_sha256,
        }
        for item in sorted(assignments, key=lambda item: item.key)
    ]
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def _validate_assignment_clusters(assignment: TaskAssignment, task_type_ids: list[str]) -> None:
    known = set(task_type_ids)
    if not assignment.cluster_ids:
        raise ValueError("partition assignment requires at least one cluster")
    if assignment.cluster_ids != sorted(set(assignment.cluster_ids)):
        raise ValueError("partition assignment clusters must be sorted and distinct")
    if len(assignment.task_archetype_ids) != len(assignment.cluster_ids):
        raise ValueError("partition assignment archetypes and clusters differ in length")
    for cluster_id, archetype_id in zip(
        assignment.cluster_ids, assignment.task_archetype_ids, strict=True
    ):
        if archetype_id not in known:
            raise ValueError("partition assignment has unknown task archetype")
        if cluster_id != task_type_ids.index(archetype_id):
            raise ValueError("partition assignment cluster and task archetype disagree")
    if not assignment.rationale.strip():
        raise ValueError("partition assignment rationale is empty")


def _validate_common(
    artifact: PartitionArtifact,
    *,
    environment: str,
    task_groups: list[str] | None,
    shared_development_pool: bool,
    train_source_split: str,
    validation_source_split: str,
    environment_asset_hashes: dict[str, str],
    environment_description_sha256: str,
) -> None:
    if artifact.environment != environment:
        raise ValueError(
            f"partition environment is {artifact.environment!r}, expected {environment!r}"
        )
    normalized_groups = None if task_groups is None else sorted(task_groups)
    if artifact.task_groups != normalized_groups:
        raise ValueError("partition task-group selection does not match this run")
    if artifact.shared_development_pool != shared_development_pool:
        raise ValueError("partition shared-pool configuration does not match environment")
    if artifact.train_source_split != train_source_split:
        raise ValueError("partition training source split does not match environment")
    if artifact.validation_source_split != validation_source_split:
        raise ValueError("partition validation source split does not match environment")
    if artifact.environment_asset_hashes != environment_asset_hashes:
        raise ValueError(
            "partition environment asset hashes do not match current assets: "
            f"artifact={sorted(artifact.environment_asset_hashes)}, "
            f"current={sorted(environment_asset_hashes)}"
        )
    if artifact.environment_description_sha256 != environment_description_sha256:
        raise ValueError("partition environment description does not match the adapter")


def _validate_clusters(artifact: PartitionArtifact) -> None:
    task_type_ids = [item.task_type_id for item in artifact.task_types]
    expected_ids = [f"type-{index:04d}" for index in range(len(task_type_ids))]
    if task_type_ids != expected_ids or not task_type_ids:
        raise ValueError("partition task type IDs are not canonical and contiguous")
    names = [item.name.casefold() for item in artifact.task_types]
    if len(set(names)) != len(names):
        raise ValueError("partition task type names are not unique")
    observed_sizes = {cluster_id: 0 for cluster_id in range(len(task_type_ids))}
    for assignment in artifact.assignments:
        _validate_assignment_clusters(assignment, task_type_ids)
        for cluster_id in assignment.cluster_ids:
            observed_sizes[cluster_id] += 1
    if artifact.cluster_sizes != observed_sizes:
        raise ValueError("partition cluster sizes do not match assignments")


def load_and_validate_partition(
    path: Path,
    *,
    environment: str,
    task_groups: list[str] | None,
    pools: OptimizationTaskPools,
    environment_asset_hashes: dict[str, str],
    environment_description_sha256: str,
) -> PartitionArtifact:
    """Validate a partition against the live task pool (every instruction re-read)."""
    if not path.is_file():
        raise FileNotFoundError(f"partition artifact not found: {path}")
    artifact = PartitionArtifact.model_validate_json(path.read_text())
    _validate_common(
        artifact,
        environment=environment,
        task_groups=task_groups,
        shared_development_pool=pools.shared_development_pool,
        train_source_split=pools.train_source_split,
        validation_source_split=pools.validation_source_split,
        environment_asset_hashes=environment_asset_hashes,
        environment_description_sha256=environment_description_sha256,
    )
    tasks = unique_pool_tasks(pools)
    if artifact.task_pool_sha256 != task_pool_hash(tasks):
        raise ValueError("partition task-pool hash does not match current task instructions")
    expected = [(task.key, instruction_hash(task.instruction)) for task in tasks]
    actual = [(item.key, item.instruction_sha256) for item in artifact.assignments]
    if actual != expected:
        raise ValueError("partition assignments do not match the current pool exactly")
    _validate_clusters(artifact)
    return artifact


def load_and_validate_partition_metadata(
    path: Path,
    *,
    environment: str,
    task_groups: list[str] | None,
    expected_tasks: dict[TaskKey, str],
    shared_development_pool: bool,
    train_source_split: str,
    validation_source_split: str,
    environment_asset_hashes: dict[str, str],
    environment_description_sha256: str,
) -> PartitionArtifact:
    """Validate a partition without replaying every environment instruction.

    Instruction hashes were captured when the partition was constructed; here their aggregate is
    checked internally while the authoritative environment manifest proves the exact task IDs and
    task types. This avoids resetting every task before each optimization run.
    """
    if not path.is_file():
        raise FileNotFoundError(f"partition artifact not found: {path}")
    artifact = PartitionArtifact.model_validate_json(path.read_text())
    _validate_common(
        artifact,
        environment=environment,
        task_groups=task_groups,
        shared_development_pool=shared_development_pool,
        train_source_split=train_source_split,
        validation_source_split=validation_source_split,
        environment_asset_hashes=environment_asset_hashes,
        environment_description_sha256=environment_description_sha256,
    )
    ordered_assignments = sorted(artifact.assignments, key=lambda item: item.key)
    if artifact.task_pool_sha256 != assignment_pool_hash(ordered_assignments):
        raise ValueError("partition task-pool hash disagrees with its assignments")
    if not artifact.shared_development_pool:
        raise ValueError("metadata-only partition validation currently requires a shared pool")
    actual_tasks = {item.key for item in ordered_assignments}
    if len(actual_tasks) != len(ordered_assignments):
        raise ValueError("partition contains duplicate split-aware task keys")
    expected_keys = set(expected_tasks)
    if actual_tasks != expected_keys:
        missing_tasks = sorted(expected_keys - actual_tasks)
        unexpected_tasks = sorted(actual_tasks - expected_keys)
        raise ValueError(
            "partition assignments do not match the authoritative task manifest: "
            f"missing={[key.canonical for key in missing_tasks]}, "
            f"unexpected={[key.canonical for key in unexpected_tasks]}"
        )
    _validate_clusters(artifact)
    return artifact
