"""Framework-neutral access to the frozen ScienceWorld task catalog."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.resources import files
import json
import os
from typing import Any


_TASK_FILES = {
    "development": "dev.json",
    "test_seen": "test_seen.json",
    "test_unseen": "test_unseen.json",
}
_TASK_FILE_SHA256 = {
    "dev.json": "bd986b372b1835739eeee78b59782a56e08d5ff2492a8bd5fed90349c5d151ce",
    "test_seen.json": "aff4333a95331dcc5add748169e69660a9aef7b0b786d120f9e6d15b219e0166",
    "test_unseen.json": "455a80fe5361c48fc7404263438b5e75bdefddecd23235a2c9cf0464e2a22a18",
}
_CATALOG_VERSION = os.environ.get("SCIENCEWORLD_CATALOG", "eto")
if _CATALOG_VERSION == "find_thermometer_full_v1":
    _TASK_FILES["development"] = "dev_find_thermometer_full_v1.json"
    _TASK_FILE_SHA256["dev_find_thermometer_full_v1.json"] = (
        "1adafd368e22b78dd70d9f663c818da0aa9e3449138c1d0441718bf2fdec6a3c"
    )
elif _CATALOG_VERSION != "eto":
    raise ValueError(f"unknown ScienceWorld catalog: {_CATALOG_VERSION!r}")

_REQUIRED_TASK_FIELDS = {
    "task_idx",
    "task_type",
    "instruction",
    "initial_observation",
    "variation_idx",
}
@dataclass(frozen=True, slots=True)
class ScienceWorldTask:
    """One immutable task from the released ScienceWorld protocol."""

    task_id: int
    task_type: str
    instruction: str
    initial_observation: str
    variation_idx: int


@dataclass(frozen=True, slots=True)
class ScienceWorldSplit:
    """One ordered, provenance-bearing frozen task split."""

    name: str
    role: str
    source: str
    source_revision: str
    tasks: tuple[ScienceWorldTask, ...]
    sha256: str


def _read_task_split(name: str, filename: str) -> ScienceWorldSplit:
    raw = files("scienceworld_env").joinpath("assets", "tasks", filename).read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    expected_hash = _TASK_FILE_SHA256[filename]
    if actual_hash != expected_hash:
        raise ValueError(
            f"ScienceWorld task-file hash mismatch for {filename}: "
            f"{actual_hash} != {expected_hash}"
        )
    payload: Any = json.loads(raw)
    expected_keys = {
        "schema_version",
        "benchmark",
        "role",
        "source",
        "source_revision",
        "tasks",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ValueError(f"invalid ScienceWorld task-file schema: {filename}")
    if payload["schema_version"] != 1 or payload["benchmark"] != "sciworld":
        raise ValueError(f"invalid ScienceWorld task-file identity: {filename}")
    if payload["role"] != name:
        raise ValueError(f"invalid ScienceWorld task-file role: {filename}")

    records = payload["tasks"]
    if not isinstance(records, list) or not records:
        raise ValueError(f"empty ScienceWorld task file: {filename}")
    tasks: list[ScienceWorldTask] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not _REQUIRED_TASK_FIELDS <= set(record):
            raise ValueError(f"invalid ScienceWorld task {index}: {filename}")
        tasks.append(
            ScienceWorldTask(
                task_id=int(record["task_idx"]),
                task_type=str(record["task_type"]),
                instruction=str(record["instruction"]),
                initial_observation=str(record["initial_observation"]),
                variation_idx=int(record["variation_idx"]),
            )
        )
    task_ids = [task.task_id for task in tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError(f"duplicate ScienceWorld task IDs: {filename}")

    return ScienceWorldSplit(
        name=name,
        role=str(payload["role"]),
        source=str(payload["source"]),
        source_revision=str(payload["source_revision"]),
        tasks=tuple(tasks),
        sha256=actual_hash,
    )


_SPLITS = {
    name: _read_task_split(name, filename) for name, filename in _TASK_FILES.items()
}
_TASKS_BY_ID = {
    task.task_id: task
    for split in _SPLITS.values()
    for task in split.tasks
}
if len(_TASKS_BY_ID) != sum(len(split.tasks) for split in _SPLITS.values()):
    raise ValueError("ScienceWorld task files contain overlapping task IDs")
if _CATALOG_VERSION == "eto" and tuple(_TASKS_BY_ID) != tuple(range(1888)):
    raise ValueError("ScienceWorld global task IDs are not the frozen contiguous ordering")
if _CATALOG_VERSION == "find_thermometer_full_v1":
    if len(_SPLITS["development"].tasks) != 2490 or len(_TASKS_BY_ID) != 2895:
        raise ValueError("expanded ScienceWorld catalog has unexpected task counts")
    _identities = [
        (task.task_type, task.variation_idx) for task in _TASKS_BY_ID.values()
    ]
    if len(set(_identities)) != len(_identities):
        raise ValueError("expanded ScienceWorld catalog has overlapping simulator variations")


def get_split(name: str) -> ScienceWorldSplit:
    """Return one immutable split by its public name."""

    try:
        return _SPLITS[name]
    except KeyError as error:
        raise ValueError(f"unknown ScienceWorld split: {name!r}") from error


def get_task(task_id: int) -> ScienceWorldTask:
    """Resolve one task by its stable global integer identity."""

    try:
        return _TASKS_BY_ID[task_id]
    except KeyError as error:
        raise ValueError(f"unknown ScienceWorld task ID: {task_id}") from error


def catalog_sha256() -> str:
    """Return a deterministic digest of ordered task semantics and provenance."""

    rows = [
        [
            split.role,
            task.task_id,
            task.task_type,
            task.variation_idx,
            task.instruction,
            task.initial_observation,
        ]
        for split in _SPLITS.values()
        for task in split.tasks
    ]
    canonical = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
