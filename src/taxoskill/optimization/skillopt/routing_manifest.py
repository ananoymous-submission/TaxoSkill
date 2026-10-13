"""Precompute per-cluster routing for fixed evaluation splits."""
from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from taxoskill.config import load_config
from taxoskill.openenv import make_openenv
from taxoskill.optimization.partitioning.artifact import PartitionArtifact
from taxoskill.optimization.partitioning.taxonomy import render_environment
from taxoskill.optimization.skillopt.router import build_routing_artifact


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--partition", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--splits", nargs="+", required=True)
    parser.add_argument("--batch", type=int, default=40)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    cfg = load_config(args.config, [])
    partition = PartitionArtifact.model_validate_json(args.partition.read_text(encoding="utf-8"))
    if partition.environment != cfg.env.name:
        raise ValueError("routing partition environment does not match the config")
    endpoint = make_openenv(cfg.env)
    try:
        records_by_split = {
            split: [dict(record) for record in endpoint.task_records(split)]
            for split in args.splits
        }
        # Sealed evaluation splits publish no instruction text in their task records; the goal
        # the actor is shown at reset is the instruction the router must read.
        for split, records in records_by_split.items():
            sealed = [record for record in records if not str(record["instruction"]).strip()]
            if sealed:
                print(f"[routing] {split}: fetching {len(sealed)} sealed instructions via reset", flush=True)
            for record in sealed:
                record["instruction"] = endpoint.reset(record["id"]).goal
    finally:
        endpoint.close()

    path = build_routing_artifact(
        records_by_split=records_by_split,
        partition=partition,
        environment=render_environment(cfg.env.name, cfg=cfg),
        output_path=args.out,
        batch=args.batch,
        workers=args.workers,
    )
    count = sum(len(records) for records in records_by_split.values())
    print(f"[routing] assigned {count} tasks across {args.splits} -> {path}")


if __name__ == "__main__":
    main()
