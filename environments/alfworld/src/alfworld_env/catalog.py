"""Framework-neutral access to the frozen ALFWorld task catalog."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.resources import files
import json
from pathlib import PurePosixPath
from typing import Any


_TASK_FILES = {
    "development": "dev.json",
    "test_seen": "test_seen.json",
    "test_unseen": "test_unseen.json",
}
_TASK_FILE_SHA256 = {
    "dev.json": "cb7f36a97ce22bd3a85faff6571be254d4c9e0fbab1a84610791f6df1c6868c3",
    "test_seen.json": "43f04ca957c4975f40e399f7e22aa12dff5bfc3fde782c95e64648b1d67deffb",
    "test_unseen.json": "5ea890a7e862a2aece519940b697a5048118fbb4e298b48614b6362d0b7ba088",
}
_REQUIRED_TASK_FIELDS = {
    "task_idx",
    "task_type",
    "instruction",
    "initial_observation",
    "gamefile",
}


@dataclass(frozen=True, slots=True)
class AlfWorldTask:
    """One immutable task from the released ALFWorld text protocol."""

    task_id: int
    task_type: str
    instruction: str
    initial_observation: str
    gamefile: str


@dataclass(frozen=True, slots=True)
class AlfWorldSplit:
    """One ordered, provenance-bearing frozen task split."""

    name: str
    role: str
    source: str
    source_revision: str
    tasks: tuple[AlfWorldTask, ...]
    sha256: str


def _validated_gamefile(value: Any, *, filename: str, index: int) -> str:
    gamefile = str(value)
    path = PurePosixPath(gamefile)
    if (
        path.is_absolute()
        or not path.parts
        or path.parts[0] != "json_2.1.1"
        or ".." in path.parts
        or path.name != "game.tw-pddl"
    ):
        raise ValueError(f"invalid ALFWorld gamefile for task {index}: {filename}")
    return gamefile


def _read_task_split(name: str, filename: str) -> AlfWorldSplit:
    raw = files("alfworld_env").joinpath("assets", "tasks", filename).read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    expected_hash = _TASK_FILE_SHA256[filename]
    if actual_hash != expected_hash:
        raise ValueError(
            f"ALFWorld task-file hash mismatch for {filename}: "
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
        raise ValueError(f"invalid ALFWorld task-file schema: {filename}")
    if payload["schema_version"] != 1 or payload["benchmark"] != "alfworld":
        raise ValueError(f"invalid ALFWorld task-file identity: {filename}")
    if payload["role"] != name:
        raise ValueError(f"invalid ALFWorld task-file role: {filename}")

    records = payload["tasks"]
    if not isinstance(records, list) or not records:
        raise ValueError(f"empty ALFWorld task file: {filename}")
    tasks: list[AlfWorldTask] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not _REQUIRED_TASK_FIELDS <= set(record):
            raise ValueError(f"invalid ALFWorld task {index}: {filename}")
        tasks.append(
            AlfWorldTask(
                task_id=int(record["task_idx"]),
                task_type=str(record["task_type"]),
                instruction=str(record["instruction"]),
                initial_observation=str(record["initial_observation"]),
                gamefile=_validated_gamefile(
                    record["gamefile"], filename=filename, index=index
                ),
            )
        )
    task_ids = [task.task_id for task in tasks]
    gamefiles = [task.gamefile for task in tasks]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError(f"duplicate ALFWorld task IDs: {filename}")
    if len(set(gamefiles)) != len(gamefiles):
        raise ValueError(f"duplicate ALFWorld gamefiles: {filename}")

    return AlfWorldSplit(
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
    raise ValueError("ALFWorld task files contain overlapping task IDs")
if tuple(sorted(_TASKS_BY_ID)) != tuple(range(57, 3884)):
    raise ValueError("ALFWorld global task IDs are not the frozen contiguous ordering")
if len({task.gamefile for task in _TASKS_BY_ID.values()}) != len(_TASKS_BY_ID):
    raise ValueError("ALFWorld task files contain overlapping gamefiles")


def get_split(name: str) -> AlfWorldSplit:
    """Return one immutable split by its public name."""

    try:
        return _SPLITS[name]
    except KeyError as error:
        raise ValueError(f"unknown ALFWorld split: {name!r}") from error


def get_task(task_id: int) -> AlfWorldTask:
    """Resolve one task by its stable global integer identity."""

    try:
        return _TASKS_BY_ID[task_id]
    except KeyError as error:
        raise ValueError(f"unknown ALFWorld task ID: {task_id}") from error


def catalog_sha256() -> str:
    """Return a deterministic digest of ordered task semantics and provenance."""

    rows = [
        [
            split.role,
            task.task_id,
            task.task_type,
            task.gamefile,
            task.instruction,
            task.initial_observation,
        ]
        for split_name in ("development", "test_seen", "test_unseen")
        for split in (_SPLITS[split_name],)
        for task in split.tasks
    ]
    canonical = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
