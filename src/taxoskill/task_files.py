"""Strict reader for one explicit frozen benchmark task file."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


TASK_FILE_ROLES = frozenset({"development", "test", "test_seen", "test_unseen"})


@dataclass(frozen=True)
class TaskFile:
    path: Path
    benchmark: str
    role: str
    source: str
    source_revision: str
    tasks: tuple[dict, ...]
    sha256: str


@dataclass(frozen=True)
class TaskPool:
    """One ordered benchmark task pool used by partitioning and analysis."""

    env: str
    task_ids: list[str]
    instructions: list[str]
    initial_observations: list[str]
    task_types: list[str]
    role: str = "development"
    source: str = ""
    source_revision: str = ""
    manifest_path: Path | None = None
    manifest_sha256: str = ""
    environment_asset_hashes: dict[str, str] = field(default_factory=dict)
    environment_description: str = ""

    def __len__(self) -> int:
        return len(self.task_ids)


def load_task_file(path: Path, *, require_role: str | None = None) -> TaskFile:
    resolved = path.resolve(strict=True)
    raw = resolved.read_bytes()
    payload = json.loads(raw)
    expected = {
        "schema_version",
        "benchmark",
        "role",
        "source",
        "source_revision",
        "tasks",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError(f"invalid explicit task file schema: {resolved}")
    if payload["schema_version"] != 1:
        raise ValueError(f"unsupported task-file schema version: {payload['schema_version']!r}")
    benchmark = str(payload["benchmark"])
    role = str(payload["role"])
    source = str(payload["source"])
    source_revision = str(payload["source_revision"])
    tasks = payload["tasks"]
    if role not in TASK_FILE_ROLES:
        raise ValueError(f"unsupported task-file role: {role!r}")
    if require_role is not None and role != require_role:
        raise ValueError(f"task loader requires role {require_role!r}, got {role!r}: {resolved}")
    if not benchmark or not source or not source_revision:
        raise ValueError("task-file identity and provenance must be non-empty")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"task file is empty or invalid: {resolved}")
    required_task_fields = {"task_idx", "task_type", "instruction", "initial_observation"}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or not required_task_fields <= set(task):
            raise ValueError(
                f"task {index} lacks required fields {sorted(required_task_fields)}: {resolved}"
            )
    task_ids = [str(task["task_idx"]) for task in tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError(f"task file contains duplicate task IDs: {resolved}")
    if role == "development" and any(not str(task.get("instruction", "")).strip() for task in tasks):
        raise ValueError(f"development task file contains an empty instruction: {resolved}")
    return TaskFile(
        path=resolved,
        benchmark=benchmark,
        role=role,
        source=source,
        source_revision=source_revision,
        tasks=tuple(tasks),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def load_manifest(
    source: str | Path,
    *,
    require_role: str | None = None,
) -> TaskPool:
    """Load one explicit frozen task-file path."""

    path = Path(source)
    task_file = load_task_file(path, require_role=require_role)
    records = task_file.tasks
    return TaskPool(
        env=task_file.benchmark,
        task_ids=[str(record["task_idx"]) for record in records],
        instructions=[str(record["instruction"]) for record in records],
        initial_observations=[str(record["initial_observation"]) for record in records],
        task_types=[str(record["task_type"]) for record in records],
        role=task_file.role,
        source=task_file.source,
        source_revision=task_file.source_revision,
        manifest_path=task_file.path,
        manifest_sha256=task_file.sha256,
    )
