"""One resumable results file per evaluation run: outcome, cost, and failure reason per task."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypedDict

from taxoskill.optimization.tasks import TaskKey
from taxoskill.run_storage import path_component, seeded_root


RESULTS_ROOT = Path("outputs/evaluations")
RESULTS_FILENAME = "results.json"
SCHEMA_VERSION = 2


class TaskRecord(TypedDict):
    solved: bool
    status: str  # success | terminal_failure | environment_truncation | step_cap
    fail_reason: str  # environment-reported reason, "" when none
    last_observation: str
    n_steps: int
    input_tokens: int
    output_tokens: int
    action_failures: dict[str, int]  # category -> count


EvaluationResults = dict[TaskKey, TaskRecord]

_FIELDS = set(TaskRecord.__annotations__)


def results_path(environment: str, run_id: str, *, seed: int = 0,
                 repeat: int | None = None, omission: float | None = None) -> Path:
    if not environment.strip():
        raise ValueError("environment must not be empty")
    if not run_id.strip():
        raise ValueError("run_id must not be empty")
    directory = seeded_root(RESULTS_ROOT, environment, seed, omission=omission) / path_component(run_id)
    if omission is not None and repeat is None:
        raise ValueError("condition-scoped evaluations require an explicit repeat")
    if repeat is not None:
        if type(repeat) is not int or repeat < 1:
            raise ValueError("evaluation repeat must be a positive integer")
        directory /= f"eval_{repeat}"
    return directory / RESULTS_FILENAME


def task_record(final: dict[str, Any], status: str, fail_reason: str) -> TaskRecord:
    """Reduce one finished episode to the record that is persisted."""
    counts: dict[str, int] = {}
    for failure in final["action_failures"]:
        counts[failure["category"]] = counts.get(failure["category"], 0) + 1
    trajectory = final["trajectory"]
    return {
        "solved": bool(final["success"]),
        "status": status,
        "fail_reason": fail_reason,
        "last_observation": trajectory[-1]["observation"][:300] if trajectory else "",
        "n_steps": int(final["step"]),
        "input_tokens": int(final["input_tokens"]),
        "output_tokens": int(final["output_tokens"]),
        "action_failures": counts,
    }


def _validate(key: TaskKey, record: object, path: Path) -> TaskRecord:
    if not isinstance(record, dict) or set(record) != _FIELDS:
        raise TypeError(f"task {key.canonical} has invalid result fields in {path}")
    if type(record["solved"]) is not bool:
        raise TypeError(f"task {key.canonical} solved must be boolean in {path}")
    for field in ("status", "fail_reason", "last_observation"):
        if not isinstance(record[field], str):
            raise TypeError(f"task {key.canonical} {field} must be a string in {path}")
    for field in ("n_steps", "input_tokens", "output_tokens"):
        if type(record[field]) is not int or record[field] < 0:
            raise TypeError(f"task {key.canonical} {field} must be a non-negative int in {path}")
    counts = record["action_failures"]
    if not isinstance(counts, dict) or any(
        not isinstance(category, str) or type(count) is not int or count < 0
        for category, count in counts.items()
    ):
        raise TypeError(f"task {key.canonical} has invalid action failure counts in {path}")
    return {field: record[field] for field in _FIELDS}  # type: ignore[return-value]


def summarize(results: EvaluationResults) -> dict[str, Any]:
    by_split: dict[str, dict[str, int]] = {}
    for key, record in results.items():
        split = by_split.setdefault(key.source_split, {"n_tasks": 0, "n_solved": 0})
        split["n_tasks"] += 1
        split["n_solved"] += int(record["solved"])
    return {
        "n_tasks": len(results),
        "n_solved": sum(record["solved"] for record in results.values()),
        "n_steps": sum(record["n_steps"] for record in results.values()),
        "input_tokens": sum(record["input_tokens"] for record in results.values()),
        "output_tokens": sum(record["output_tokens"] for record in results.values()),
        "n_action_failures": sum(
            sum(record["action_failures"].values()) for record in results.values()
        ),
        "test_sets": {name: by_split[name] for name in sorted(by_split)},
    }


def write_results(environment: str, run_id: str, results: EvaluationResults, *, seed: int = 0,
                  repeat: int | None = None, omission: float | None = None) -> Path:
    """Atomically persist every finished task of one evaluation run."""
    path = results_path(environment, run_id, seed=seed, repeat=repeat, omission=omission)
    path.parent.mkdir(parents=True, exist_ok=True)
    tasks: dict[str, dict[str, TaskRecord]] = {}
    for key in sorted(results):
        tasks.setdefault(key.source_split, {})[str(key.task_idx)] = results[key]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "summary": summarize(results),
        "tasks": tasks,
    }
    if omission is not None:
        payload["omission"] = omission
    if repeat is not None:
        payload["repeat"] = repeat
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def load_results(environment: str, run_id: str, *, seed: int = 0,
                 repeat: int | None = None, omission: float | None = None) -> EvaluationResults:
    """Load one run's results, failing on any invalid content."""
    path = results_path(environment, run_id, seed=seed, repeat=repeat, omission=omission)
    if not path.is_file():
        raise FileNotFoundError(f"evaluation results not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    scope_fields = {"repeat"} if repeat is not None else set()
    scope_fields |= {"omission"} if omission is not None else set()
    required = {"schema_version", "summary", "tasks"} | scope_fields
    if not isinstance(raw, dict) or set(raw) not in (required, required | {"seed"}):
        raise TypeError(f"evaluation results have invalid top-level fields: {path}")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported evaluation results schema in {path}")
    if raw.get("seed", 0) != seed:
        raise ValueError(f"evaluation seed does not match requested seed {seed}: {path}")
    if raw.get("repeat") != repeat or (repeat is not None and type(raw["repeat"]) is not int):
        raise ValueError(f"evaluation repeat does not match requested repeat {repeat}: {path}")
    if raw.get('omission') != omission or (omission is not None and type(raw['omission']) not in (int, float)):
        raise ValueError(f'evaluation omission differs from requested target: {path}')
    results: EvaluationResults = {}
    for test_set, records in raw["tasks"].items():
        if not isinstance(test_set, str) or not test_set or not isinstance(records, dict):
            raise TypeError(f"invalid test set group in {path}")
        for raw_task_id, record in records.items():
            if not isinstance(raw_task_id, str) or not raw_task_id.isdigit():
                raise ValueError(f"invalid task id {raw_task_id!r} in {path}")
            key = TaskKey(test_set, int(raw_task_id))
            results[key] = _validate(key, record, path)
    if raw["summary"] != summarize(results):
        raise ValueError(f"evaluation results summary does not match tasks in {path}")
    return results


def merge_results(environment: str, run_ids: list[str], *, seed: int = 0,
                  repeat: int | None = None, omission: float | None = None) -> EvaluationResults:
    """Merge resumable runs and reject contradictory records for the same task."""
    merged: EvaluationResults = {}
    for run_id in run_ids:
        for key, record in load_results(environment, run_id, seed=seed, repeat=repeat, omission=omission).items():
            if key in merged and merged[key] != record:
                raise ValueError(
                    f"conflicting results for task {key.canonical} across resumed evaluations"
                )
            merged[key] = record
    return merged
