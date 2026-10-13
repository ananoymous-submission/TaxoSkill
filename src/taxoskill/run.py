"""Entrypoint: run the single-attempt ReAct loop over frozen evaluation splits.

    export DEEPSEEK_API_KEY=...
    python -m taxoskill.run --config configs/experiments/<environment>/base.yaml
    python -m taxoskill.run --config other.yaml workers=8 model.rollout.max_tokens=4096

One MLflow run per invocation: the resolved config as params, prompt-asset hashes as tags,
aggregate outcomes as metrics — and one trace per task (a task-N span with one child span per
model call from the OpenAI autolog), browsable in the Traces UI.

Parallelism: `workers` tasks in flight via a thread pool. Each task runs fully synchronously
inside its worker thread. Every task owns one environment and closes it in ``finally``; all
workers share one thread-safe model client. The pool size is also the provider
request-concurrency limit used by this process.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from concurrent.futures import as_completed
from contextlib import nullcontext
from pathlib import Path

import mlflow
from dotenv import load_dotenv

from taxoskill.agents.prompt import prompt_hashes
from taxoskill.concurrency import FailFastThreadPoolExecutor
from taxoskill.agents.react import episode_status, run_episode, run_task
from taxoskill.config import RunCfg, load_config
from taxoskill.evaluation_results import results_path
from taxoskill.run_storage import run_name as canonical_run_name
from taxoskill.run_storage import validate_artifact_scope
from taxoskill.evaluation_results import (
    EvaluationResults,
    merge_results,
    summarize,
    task_record,
    write_results,
)
from taxoskill.llm import Model, actor_model
from taxoskill.openenv import make_openenv
from taxoskill.optimization.tasks import TaskKey

from taxoskill.tracking import flatten_params, setup_tracking


def _evaluation_task_keys(
    env: object,
    test_sets: Sequence[str],
    task_indices: Callable[[object, str], list[int]],
) -> list[TaskKey]:
    keys = [
        TaskKey(test_set, task_idx)
        for test_set in test_sets
        for task_idx in task_indices(env, test_set)
    ]
    if len(set(keys)) != len(keys):
        raise ValueError("evaluation test sets contain duplicate split-scoped task identities")
    return keys


def _evaluation_metrics(
    results: EvaluationResults,
    test_sets: Sequence[str],
) -> dict[str, float | int]:
    metrics: dict[str, float | int] = {}
    for test_set in test_sets:
        outcomes = [
            outcome
            for key, outcome in results.items()
            if key.source_split == test_set
        ]
        if not outcomes:
            raise ValueError(f"evaluation has no results for test set {test_set!r}")
        metrics[f"{test_set}_n_tasks"] = len(outcomes)
        metrics[f"{test_set}_solve_rate"] = (
            sum(outcome["solved"] for outcome in outcomes) / len(outcomes)
        )
    return metrics


def _load_procedural_memory(
    cfg: RunCfg, procedural_memory_file: Path | None = None
) -> str:
    """Resolve the explicit memory string for the selected runtime condition."""
    a = cfg.agent
    if procedural_memory_file is not None:
        if a.name != "skillopt":
            raise ValueError("--procedural-memory-file requires agent.name=skillopt")
        path = procedural_memory_file.resolve(strict=True)
        memory = path.read_text(encoding="utf-8")
        if not memory.strip():
            state_path = path.parent / "runtime_state.json"
            summary_path = path.parent / "summary.json"
            if path.name == "best_skill.md" and state_path.is_file() and summary_path.is_file():
                state = json.loads(state_path.read_text(encoding="utf-8"))
                if state.get("best_origin") == "initial_skill" and state.get("best_step") == 0:
                    return ""
            raise ValueError(f"procedural-memory file is empty: {path}")
        return memory
    if a.percluster_skill_dir is not None:
        return ""
    if a.name == "react":
        return ""
    raise ValueError(
        "agent.name=skillopt requires --procedural-memory-file or per-cluster routing"
    )


def _run_one(
    task_idx: int,
    cfg: RunCfg,
    model: Model,
    run_id: str | None,
    memory: str,
    track_with_mlflow: bool,
    task_records: dict[str, list[dict]],
):
    """Run one task with an environment that is always released afterward."""
    if track_with_mlflow and mlflow.active_run() is None:
        if run_id is None:
            raise ValueError("tracked evaluation requires an MLflow run ID")
        mlflow.start_run(run_id=run_id)
    env = make_openenv(cfg.env, task_records=task_records)
    try:
        runner = run_task if track_with_mlflow else run_episode
        return runner(env, model, cfg.react, memory, task_idx)
    finally:
        env.close()


def _per_cluster_memory(
    cfg: RunCfg,
    probe: object,
) -> dict[TaskKey, str]:
    """Build ``{TaskKey: skill}`` by assigning every evaluation task to its cluster via the
    taxonomy and resolving that cluster's learned best skill."""
    from taxoskill.optimization.partitioning.artifact import PartitionArtifact
    from taxoskill.optimization.skillopt.router import (
        assign_evaluation_to_clusters,
        load_routing_artifact,
        skill_for_cluster,
    )

    if cfg.optimization.partition_artifact is None:
        raise ValueError(
            "per-cluster evaluation requires optimization.partition_artifact"
        )
    artifact = PartitionArtifact.model_validate_json(
        Path(cfg.optimization.partition_artifact).read_text()
    )
    if artifact.environment != cfg.env.name:
        raise ValueError(
            f"partition environment {artifact.environment!r} does not match {cfg.env.name!r}"
        )
    records_by_split: dict[str, list[dict]] = {}
    for test_set in cfg.evaluation.test_sets:
        records_by_split[test_set] = [
            dict(record) for record in probe.task_records(test_set)  # type: ignore[attr-defined]
        ]
    if cfg.agent.percluster_routing_artifact is not None:
        expected_keys = {
            TaskKey(test_set, int(record["id"]))
            for test_set, records in records_by_split.items()
            for record in records
        }
        routing = load_routing_artifact(
            cfg.agent.percluster_routing_artifact,
            expected_keys=expected_keys,
            partition=artifact,
        )
        print(
            f"[per-cluster] loaded cached routing for {len(routing)} evaluation tasks"
        )
    else:
        from taxoskill.optimization.partitioning.taxonomy import render_environment

        routing = assign_evaluation_to_clusters(
            records_by_split=records_by_split,
            partition=artifact,
            environment=render_environment(cfg.env.name, cfg=cfg),
        )
    if cfg.agent.percluster_skill_dir is None:
        raise ValueError("per-cluster evaluation requires agent.percluster_skill_dir")
    skill_root = Path(cfg.agent.percluster_skill_dir)
    memories = {
        key: skill_for_cluster(skill_root, cluster_id)
        for key, cluster_id in routing.items()
    }
    print(
        f"[per-cluster] routed {len(memories)} evaluation tasks to clusters; "
        f"verified skills for all (no unassigned tasks)"
    )
    return memories


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--procedural-memory-file", type=Path)
    parser.add_argument("--mlflow", action="store_true", help="opt in to MLflow tracking")
    parser.add_argument("overrides", nargs="*", help="dotted configuration overrides")
    args = parser.parse_args()
    cfg = load_config(args.config, args.overrides)

    if args.procedural_memory_file is not None:
        validate_artifact_scope(args.procedural_memory_file.parent,
                                environment=cfg.env.name, seed=cfg.seed, omission=cfg.omission)
    if cfg.agent.percluster_skill_dir is not None:
        validate_artifact_scope(Path(cfg.agent.percluster_skill_dir),
                                environment=cfg.env.name, seed=cfg.seed, omission=cfg.omission)
    track_with_mlflow = args.mlflow
    if track_with_mlflow:
        setup_tracking(cfg.tracking)
        mlflow.openai.autolog(exclusive=False, log_traces=True)
    if cfg.agent.name == "react":
        condition = "no_skill"
    elif cfg.agent.percluster_skill_dir is not None:
        condition = "per_cluster_taxoskill"
    else:
        selection = cfg.optimization.train_selection
        if args.procedural_memory_file is not None:
            source_config = args.procedural_memory_file.parent / "resolved_config.json"
            if source_config.is_file():
                source = json.loads(source_config.read_text(encoding="utf-8"))
                if source["seed"] != cfg.seed:
                    raise ValueError("global skill seed differs from evaluation seed")
                selection = source["optimization"]["train_selection"]
        condition = "global_taxoskill" if selection == "cluster" else "global_random"
    run_name = canonical_run_name(condition, cfg.seed)
    storage_scope = {"seed": cfg.seed, "omission": cfg.omission, "repeat": cfg.evaluation.repeat}
    if cfg.evaluation.resume_from not in (None, run_name):
        raise ValueError(f"resume_from must be {run_name!r} for this condition and seed")
    run_dir = results_path(cfg.env.name, run_name, **storage_scope).parent
    if cfg.evaluation.resume_from is not None:
        if not run_dir.is_dir():
            raise FileNotFoundError(f"evaluation resume output does not exist: {run_dir}")
        validate_artifact_scope(run_dir, environment=cfg.env.name, seed=cfg.seed,
                                repeat=cfg.evaluation.repeat, omission=cfg.omission)
    elif run_dir.exists():
        raise FileExistsError(f"evaluation output already exists: {run_dir}")

    memory = _load_procedural_memory(cfg, args.procedural_memory_file)

    run_context = mlflow.start_run(run_name=run_name) if track_with_mlflow else nullcontext(None)
    with run_context as run:
        run_id = run_name
        if track_with_mlflow:
            mlflow.log_params(flatten_params(cfg.model_dump()))
        run_dir.mkdir(parents=True, exist_ok=cfg.evaluation.resume_from is not None)
        (run_dir / "resolved_config.json").write_text(
            cfg.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        (run_dir / "run_metadata.json").write_text(
            json.dumps({**storage_scope, "procedural_memory_file": (
                str(args.procedural_memory_file) if args.procedural_memory_file else None
            )}, indent=2) + "\n", encoding="utf-8"
        )
        model = actor_model(cfg)
        # A short-lived probe verifies the environment layout and resolves full frozen test sets.
        probe = make_openenv(cfg.env)
        try:
            if track_with_mlflow:
                mlflow.set_tags(prompt_hashes(probe.agent_context()))
                if cfg.agent.name == "skillopt":
                    from taxoskill.optimization.environment import adapter_for_environment

                    mlflow.set_tags(
                        adapter_for_environment(cfg.env.name).asset_hashes(probe)
                    )
            task_keys = _evaluation_task_keys(
                probe,
                cfg.evaluation.test_sets,
                lambda env, test_set: env.task_indices(test_set),
            )
            task_records = {
                test_set: probe.task_records(test_set)
                for test_set in cfg.evaluation.test_sets
            }
            # Per-cluster skill routing: assign every evaluation task to its cluster and resolve
            # that cluster's skill, while the probe is live. Requires agent.percluster_skill_dir.
            per_cluster_memories: dict[TaskKey, str] | None = None
            if cfg.agent.percluster_skill_dir is not None:
                per_cluster_memories = _per_cluster_memory(cfg, probe)
        finally:
            probe.close()
        requested_task_keys = task_keys
        results: EvaluationResults = {}
        if cfg.evaluation.resume_from:
            resume_run_ids = cfg.evaluation.resume_from.split(",")
            results = merge_results(cfg.env.name, resume_run_ids, **storage_scope)
            unexpected = set(results).difference(requested_task_keys)
            if unexpected:
                raise ValueError(
                    "resumed evaluation contains tasks outside the requested task set: "
                    f"{[key.canonical for key in sorted(unexpected)]}"
                )
            task_keys = [key for key in requested_task_keys if key not in results]
            print(
                f"[taxoskill] resume: {len(results)} tasks already completed, "
                f"{len(task_keys)} to run"
            )
            if not task_keys:
                raise ValueError("resume_from covers the entire task set — nothing to run")
        write_results(cfg.env.name, run_id, results, **storage_scope)

        with FailFastThreadPoolExecutor(max_workers=cfg.workers) as pool:
            futures = {
                pool.submit(
                    _run_one,
                    task_key.task_idx,
                    cfg,
                    model,
                    run.info.run_id if track_with_mlflow else None,
                    (
                        per_cluster_memories[task_key]
                        if per_cluster_memories is not None
                        else memory
                    ),
                    track_with_mlflow,
                    task_records,
                ): task_key
                for task_key in task_keys
            }
            for fut in as_completed(futures):
                task_key = futures[fut]
                final = fut.result()  # a task failure raises here — no silent skips
                record = task_record(
                    final,
                    status=episode_status(final),
                    fail_reason=final["diagnostics"].get("fail_reason", ""),
                )
                results[task_key] = record
                write_results(cfg.env.name, run_id, results, **storage_scope)
                summary = summarize(results)
                if track_with_mlflow:
                    mlflow.log_metrics(
                        {
                            "n_completed": summary["n_tasks"],
                            "n_solved": summary["n_solved"],
                            "live_solve_rate": summary["n_solved"] / summary["n_tasks"],
                            "n_action_failures": summary["n_action_failures"],
                        },
                        step=summary["n_tasks"],
                    )
                print(
                    f"[taxoskill] task {task_key.canonical}: {record['status']}"
                    + (f" ({record['fail_reason']})" if record["fail_reason"] else "")
                )

        missing = set(requested_task_keys).difference(results)
        if missing:
            raise RuntimeError(
                "evaluation finished with missing task results: "
                f"{[key.canonical for key in sorted(missing)]}"
            )
        final_path = write_results(cfg.env.name, run_id, results, **storage_scope)
        summary = summarize(results)
        if track_with_mlflow:
            mlflow.log_artifact(str(final_path), "evaluation")
            mlflow.log_metrics(
                {
                    "n_tasks": summary["n_tasks"],
                    "n_tasks_this_invocation": len(task_keys),
                    "solve_rate": summary["n_solved"] / summary["n_tasks"],
                    "input_tokens": summary["input_tokens"],
                    "output_tokens": summary["output_tokens"],
                    "n_steps": summary["n_steps"],
                    "n_action_failures": summary["n_action_failures"],
                    **_evaluation_metrics(results, cfg.evaluation.test_sets),
                }
            )
        print(
            f"[taxoskill] done -> run {run_id} · "
            f"solved {summary['n_solved']}/{summary['n_tasks']} -> {final_path}"
        )


if __name__ == "__main__":
    main()
