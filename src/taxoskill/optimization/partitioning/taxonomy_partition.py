"""Export a TnT-LLM taxonomy (``taxonomy.py`` output) as the frozen ``partition.json`` SkillOpt consumes.

    python -m taxoskill.optimization.partitioning.taxonomy_partition <environment>

The taxonomy labels are keyed by the manifest's task ids (``taxoskill.task_files.load_manifest``); the
partition is keyed by the environment's ``TaskKey`` and pinned to the live optimization pool, the
environment assets and the environment description, exactly like the clustering export. Every task
in the pool must carry a taxonomy label; the pool is the authority (tasks the taxonomy labelled but
the pool does not contain are simply not exported).
Optimizer-facing selection always allocates train and validation budgets uniformly across the
represented taxonomy clusters.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from taxoskill.config import load_config
from taxoskill.optimization.environment import adapter_for_environment
from taxoskill.optimization.partitioning.artifact import (
    PartitionArtifact,
    TaskArchetype,
    TaskAssignment,
    environment_description_hash,
    instruction_hash,
    load_and_validate_partition,
    sha256_bytes,
    task_pool_hash,
    unique_pool_tasks,
)
from taxoskill.optimization.tasks import OptimizationTask

def _manifest_key(task: OptimizationTask) -> str:
    """The manifest task id (the taxonomy label key) for a pool task."""
    return str(task.task_idx)


def export(env: str, taxonomy_labels: Path, out: Path, *, config: Path, seed: int) -> Path:
    adapter = adapter_for_environment(env)
    cfg = load_config(config, [f"env.name={env}"])
    payload = json.loads(taxonomy_labels.read_text())
    if payload.get("method", "").startswith("tnt-llm") is False or "task_types" not in payload:
        raise ValueError(f"{taxonomy_labels} is not a taxonomy labels.json")
    types = payload["task_types"]
    labels = {str(k): int(v) for k, v in payload["labels"].items()}

    probe = adapter.make_env(cfg.env)
    try:
        pools = adapter.optimization_task_pools(probe, task_groups=None)
        asset_hashes = adapter.asset_hashes(probe)
        description_sha256 = environment_description_hash(
            adapter.environment_description(probe)
        )
    finally:
        probe.close()
    tasks = unique_pool_tasks(pools)

    assignments: list[TaskAssignment] = []
    sizes = {c: 0 for c in range(len(types))}
    for task in tasks:
        key = _manifest_key(task)
        if key not in labels:
            raise ValueError(f"pool task {task.key.canonical} (manifest id {key}) has no taxonomy label")
        label = labels[key]
        sizes[label] += 1
        assignments.append(TaskAssignment(
            task_idx=task.task_idx,
            source_split=task.source_split,
            instruction_sha256=instruction_hash(task.instruction),
            cluster_ids=[label],
            task_archetype_ids=[f"type-{label:04d}"],
            rationale=f"tnt-llm assignment: {types[label]['name']}",
        ))
    empty = [types[c]["name"] for c, n in sizes.items() if n == 0]
    if empty:
        # the taxonomy covers the whole manifest; the optimization pool may be a subset of it
        print(f"[taxonomy_partition] taxonomy types with no task in the optimization pool: {empty}")

    pool_hash = task_pool_hash(tasks)
    partition_id = sha256_bytes(json.dumps(
        {"env": env, "seed": seed, "pool": pool_hash, "labels": [a.cluster_ids[0] for a in assignments]},
        sort_keys=True, separators=(",", ":"),
    ).encode())[:20]
    artifact = PartitionArtifact(
        schema_version=10,
        partition_id=partition_id,
        method=(
            "tnt-llm taxonomy (generate/update -> preliminary assign -> "
            "assignment-aware review -> assign)"
        ),
        environment=env,
        seed=seed,
        task_groups=None,
        shared_development_pool=pools.shared_development_pool,
        train_source_split=pools.train_source_split,
        validation_source_split=pools.validation_source_split,
        environment_asset_hashes=asset_hashes,
        environment_description_sha256=description_sha256,
        task_pool_sha256=pool_hash,
        task_types=[
            TaskArchetype(task_type_id=f"type-{c:04d}", name=t["name"], definition=t["definition"])
            for c, t in enumerate(types)
        ],
        assignments=sorted(assignments, key=lambda a: a.key),
        cluster_sizes=sizes,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(artifact.model_dump_json(indent=2) + "\n")
    # round-trip through the strict validator against the live pool
    load_and_validate_partition(
        out, environment=env, task_groups=None, pools=pools,
        environment_asset_hashes=asset_hashes,
        environment_description_sha256=description_sha256,
    )
    return out


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("env")
    ap.add_argument("--config", type=Path, default=Path("config.yaml"))
    ap.add_argument("--labels", type=Path, default=None, help="taxonomy labels.json (default outputs/partitions/taxonomy/<env>/labels.json)")
    ap.add_argument("--out", type=Path, default=None, help="default outputs/partitions/taxonomy/<env>/partition.json")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    base = Path("outputs/partitions/taxonomy") / args.env
    labels = args.labels or base / "labels.json"
    out = args.out or base / "partition.json"
    path = export(args.env, labels, out, config=args.config, seed=args.seed)
    print(f"[taxonomy_partition] wrote and validated {path}")
    print(f"[taxonomy_partition] use in config: optimization.partition_artifact: {path}")


if __name__ == "__main__":
    main()
