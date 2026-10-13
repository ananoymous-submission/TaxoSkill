"""Generic endpoint-discovered task pools for partitioning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taxoskill.config import load_config
from taxoskill.openenv import make_openenv
from taxoskill.task_files import TaskPool


def _development_split(endpoint: Any) -> dict[str, Any]:
    matches = [
        dict(split)
        for split in endpoint.list_splits()
        if split.get("name") == "development"
    ]
    if len(matches) != 1:
        raise ValueError(
            "partition endpoint must expose exactly one development split, "
            f"found {len(matches)}"
        )
    split = matches[0]
    if split.get("role") != "development":
        raise ValueError("partition endpoint development split has the wrong role")
    digest = split.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("partition endpoint development split has no SHA-256")
    return split


def task_pool_from_endpoint(endpoint: Any, *, expected_env: str) -> TaskPool:
    """Build an immutable instruction pool using discovery only, never reset."""

    split = _development_split(endpoint)
    records = [dict(record) for record in endpoint.task_records("development")]
    if len(records) != int(split.get("num_tasks", -1)):
        raise ValueError(
            "partition endpoint development count mismatch: "
            f"{len(records)} != {split.get('num_tasks')}"
        )
    task_ids = [str(record.get("id")) for record in records]
    instructions = [str(record.get("instruction", "")) for record in records]
    if not records or len(set(task_ids)) != len(task_ids):
        raise ValueError("partition endpoint returned empty or duplicate development tasks")
    if any(not instruction.strip() for instruction in instructions):
        raise ValueError("partition endpoint returned an empty development instruction")
    digest = str(split["sha256"])
    for record in records:
        record_digest = record.get("catalog_sha256")
        if record_digest is not None and str(record_digest) != digest:
            raise ValueError("partition endpoint task catalog hash differs from split hash")

    metadata = dict(endpoint.agent_context().metadata)
    description = str(metadata.get("description", "")).strip()
    if not description:
        raise ValueError("partition endpoint metadata has an empty description")
    source_revision = str(split.get("source_revision", "")).strip()
    if not source_revision:
        raise ValueError("partition endpoint development split has no source revision")
    return TaskPool(
        env=expected_env,
        task_ids=task_ids,
        instructions=instructions,
        initial_observations=[""] * len(records),
        task_types=[str(record.get("task_type") or "unspecified") for record in records],
        role="development",
        source=str(metadata.get("documentation_url") or metadata.get("name") or expected_env),
        source_revision=source_revision,
        manifest_path=None,
        manifest_sha256=digest,
        environment_asset_hashes={"development_task_file": digest},
        environment_description=description,
    )


def load_endpoint_pool(config_path: str | Path) -> TaskPool:
    """Discover one config's canonical development pool and close the probe."""

    config = load_config(Path(config_path), [])
    endpoint = make_openenv(config.env)
    try:
        return task_pool_from_endpoint(endpoint, expected_env=config.env.name)
    finally:
        endpoint.close()
