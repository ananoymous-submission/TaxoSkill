"""Per-cluster skill router: assign evaluation tasks to discovered clusters and resolve the
per-task procedural memory to ONLY that cluster's learned best skill.

This decouples sampling from skill specialization. Training learns one skill per discovered
cluster (see ``taxoskill.optimization.skillopt.induction --cluster <id>``, which writes each cluster's
best skill under ``outputs/skillopt/<env>/seed_<n>/percluster/cluster_<id>/``). At evaluation every task is
assigned to exactly one cluster via the SAME label-free taxonomy used to build the partition, and
the injected procedural memory is that cluster's own skill -- never a global document.

Label-free contract: cluster assignment uses task instructions + the discovered taxonomy type
names/definitions, never official labels. A task that cannot be assigned to a known cluster is a
hard error (no silent fallback to a default or global skill).
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from taxoskill.optimization.partitioning.artifact import PartitionArtifact
from taxoskill.optimization.partitioning.taxonomy import ASSIGNMENT_MODEL, assign
from taxoskill.task_files import TaskPool
from taxoskill.optimization.tasks import TaskKey


def _cluster_id_of(partition: PartitionArtifact, type_name: str) -> int:
    for task_type in partition.task_types:
        if task_type.name == type_name:
            return int(task_type.task_type_id.removeprefix("type-"))
    raise ValueError(
        f"taxonomy assigned an unknown type name {type_name!r}; "
        "the per-cluster router refuses to route an unassignable task"
    )


def _canonical_records(
    records_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[tuple[str, int, str]]:
    records: list[tuple[str, int, str]] = []
    seen: set[TaskKey] = set()
    for split in sorted(records_by_split):
        for record in records_by_split[split]:
            task_idx = int(record["id"])
            key = TaskKey(split, task_idx)
            if key in seen:
                raise ValueError(f"per-cluster router received duplicate task {key.canonical}")
            seen.add(key)
            instruction = str(record["instruction"])
            if not instruction.strip():
                raise ValueError("per-cluster router cannot assign a task with an empty instruction")
            records.append((split, task_idx, instruction))
    if not records:
        raise ValueError("per-cluster router requires evaluation task records")
    return records


def routing_input_fingerprint(
    records_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
) -> str:
    payload = json.dumps(
        _canonical_records(records_by_split),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assign_evaluation_to_clusters(
    *,
    records_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
    partition: PartitionArtifact,
    environment: str,
    batch: int = 40,
    workers: int = 8,
) -> dict[TaskKey, int]:
    """Assign evaluation records to discovered clusters using the label-free taxonomy.

    ``records_by_split`` maps a test-set/split name to the task records the endpoint serves (each
    must carry ``id`` and ``instruction``). Returns ``{TaskKey(split, id): cluster_id}``.
    ``assign`` is deepseek-v4-flash over the frozen taxonomy types; it never sees official labels.
    """
    records = _canonical_records(records_by_split)
    canonical_ids = [f"{split}:{task_idx}" for split, task_idx, _ in records]
    instructions = [instruction for _, _, instruction in records]
    pool = TaskPool(
        env=partition.environment,
        task_ids=canonical_ids,
        instructions=instructions,
        initial_observations=[""] * len(records),
        task_types=[""] * len(records),
        role="evaluation",  # instruction-only assignment; role is irrelevant
        source="percluster-router",
        source_revision="",
        manifest_path=None,
        manifest_sha256="",
        environment_asset_hashes={},
        environment_description="",
    )
    labeled = assign(
        pool,
        [task_type.model_dump() for task_type in partition.task_types],
        batch=batch,
        workers=workers,
        environment=environment,
    )
    routing: dict[TaskKey, int] = {}
    for canonical_id, (split, task_idx, _) in zip(canonical_ids, records, strict=True):
        type_name = labeled[canonical_id]
        try:
            cluster = _cluster_id_of(partition, type_name)
        except ValueError as error:
            raise ValueError(
                f"task {split}:{task_idx} assigned to unknown taxonomy type "
                f"{type_name!r}; refusing to run"
            ) from error
        routing[TaskKey(split, task_idx)] = cluster
    return routing


def build_routing_artifact(
    *,
    records_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
    partition: PartitionArtifact,
    environment: str,
    output_path: str | Path,
    batch: int = 40,
    workers: int = 8,
) -> Path:
    """Assign all evaluation tasks once and persist a provenance-pinned routing artifact."""
    routing = assign_evaluation_to_clusters(
        records_by_split=records_by_split,
        partition=partition,
        environment=environment,
        batch=batch,
        workers=workers,
    )
    artifact = {
        "schema_version": 1,
        "environment": partition.environment,
        "partition_id": partition.partition_id,
        "assignment_model": ASSIGNMENT_MODEL,
        "input_fingerprint": routing_input_fingerprint(records_by_split),
        "splits": sorted(records_by_split),
        "assignments": [
            {
                "source_split": key.source_split,
                "task_idx": key.task_idx,
                "cluster_id": routing[key],
            }
            for key in sorted(routing)
        ],
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return path


def load_routing_artifact(
    path: str | Path,
    *,
    partition: PartitionArtifact,
    records_by_split: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    expected_keys: set[TaskKey] | None = None,
) -> dict[TaskKey, int]:
    """Load cached routing and reject stale tasks, taxonomy, or malformed assignments."""
    path = Path(path)
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("environment") != partition.environment:
        raise ValueError("routing artifact environment does not match the partition")
    if artifact.get("partition_id") != partition.partition_id:
        raise ValueError("routing artifact partition does not match the frozen taxonomy")
    if records_by_split is not None:
        expected_fingerprint = routing_input_fingerprint(records_by_split)
        if artifact.get("input_fingerprint") != expected_fingerprint:
            raise ValueError("routing artifact input fingerprint does not match evaluation tasks")
        record_keys = {
            TaskKey(split, task_idx)
            for split, task_idx, _ in _canonical_records(records_by_split)
        }
        if expected_keys is not None and expected_keys != record_keys:
            raise ValueError("routing expected keys disagree with evaluation records")
        resolved_expected_keys = record_keys
    elif expected_keys is not None:
        resolved_expected_keys = expected_keys
    else:
        raise ValueError("routing validation requires records or expected task keys")

    valid_clusters = {
        int(task_type.task_type_id.removeprefix("type-"))
        for task_type in partition.task_types
    }
    routing: dict[TaskKey, int] = {}
    for row in artifact.get("assignments", []):
        key = TaskKey(str(row["source_split"]), int(row["task_idx"]))
        cluster = int(row["cluster_id"])
        if key in routing:
            raise ValueError(f"routing artifact contains duplicate task {key.canonical}")
        if cluster not in valid_clusters:
            raise ValueError(f"routing artifact contains unknown cluster {cluster}")
        routing[key] = cluster
    if set(routing) != resolved_expected_keys:
        raise ValueError("routing artifact assignments do not match evaluation tasks")
    return routing


def skill_for_cluster(skill_root: Path, cluster_id: int) -> str:
    """Return the accepted skill, or explicit no-skill memory for a marked cluster."""
    split_file = skill_root / f"cluster_{cluster_id}.md"
    if split_file.is_file():
        skill = split_file.read_text(encoding="utf-8")
        if not skill.strip():
            raise ValueError(f"split skill for cluster {cluster_id} is empty")
        return skill
    cluster_dir = skill_root / f"cluster_{cluster_id}"
    if (cluster_dir / "NO_SKILL").is_file():
        return ""
    candidates = ([cluster_dir / "best_skill.md"] if (cluster_dir / "best_skill.md").is_file()
                  else sorted(cluster_dir.glob("*/best_skill.md")))
    if not candidates:
        raise FileNotFoundError(
            f"no learned skill for cluster {cluster_id} under {cluster_dir}; "
            "run `induction --cluster <id>` first or add an explicit NO_SKILL marker"
        )
    # A run dir may hold multiple tries; the latest (best) one is the authoritative best skill.
    skill = candidates[-1].read_text(encoding="utf-8")
    if not skill.strip():
        raise ValueError(f"learned skill for cluster {cluster_id} is empty")
    return skill


__all__ = [
    "assign_evaluation_to_clusters",
    "build_routing_artifact",
    "load_routing_artifact",
    "routing_input_fingerprint",
    "skill_for_cluster",
]