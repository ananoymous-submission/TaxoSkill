"""Train one environment-owned procedural-memory string with official SkillOpt."""

from __future__ import annotations

import argparse
import json
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import mlflow
from dotenv import load_dotenv
from skillopt.engine import ReflACTTrainer

from taxoskill.config import RunCfg, load_config
from taxoskill.run_storage import skillopt_root, run_name as canonical_run_name
from taxoskill.run_storage import validate_artifact_scope
from taxoskill.llm import (
    actor_model,
    configure_skillopt_backend,
    optimizer_request_context,
    run_optimizer_preflight,
)
from taxoskill.optimization.environment import adapter_for_environment
from taxoskill.optimization.candidate_pool import load_candidate_pool
from taxoskill.optimization.partitioning.artifact import sha256_file
from taxoskill.optimization.resolver import resolve_optimization_data
from taxoskill.optimization.skillopt.artifact import SkillOptArtifact
from taxoskill.optimization.skillopt.adapter import (
    ReActSkillOptAdapter,
    selected_task_records,
)
from taxoskill.optimization.skillopt.dataloader import SelectedTaskDataLoader
from taxoskill.tracking import setup_tracking


def _capacity_aware_percluster_config(cfg: RunCfg, *, train_size: int) -> RunCfg:
    """Cap longitudinal samples to the selected local training pool."""
    if cfg.optimization.cluster_id is None:
        return cfg
    if train_size <= 0:
        raise ValueError("per-cluster SkillOpt requires a non-empty training pool")
    if not (cfg.skillopt.use_slow_update or cfg.skillopt.use_meta_skill):
        return cfg
    effective_samples = min(cfg.skillopt.slow_update_samples, train_size)
    return cfg.model_copy(update={
        "skillopt": cfg.skillopt.model_copy(update={
            "slow_update_samples": effective_samples,
        })
    })


def _trainer_config(
    cfg: RunCfg,
    *,
    run_dir: Path,
    validation_size: int,
    initial_skill_path: Path,
) -> dict[str, Any]:
    skillopt = cfg.skillopt
    return {
        "out_root": str(run_dir),
        "env": cfg.env.name,
        "skill_init": str(initial_skill_path),
        "model_backend": "openai_compatible",
        "optimizer_backend": "openai_compatible",
        "target_backend": "openai_compatible",
        "optimizer_model": cfg.optimizer_model.model,
        "target_model": cfg.actor_model.model,
        "reasoning_effort": skillopt.optimizer.reasoning_effort,
        "num_epochs": skillopt.num_epochs,
        "batch_size": skillopt.batch_size,
        "accumulation": skillopt.accumulation,
        "seed": cfg.seed,
        "minibatch_size": skillopt.reflection_minibatch_size,
        "merge_batch_size": skillopt.merge_batch_size,
        "analyst_workers": skillopt.analyst_workers,
        "failure_only": skillopt.failure_only,
        "edit_budget": skillopt.edit_budget,
        "min_edit_budget": skillopt.min_edit_budget,
        "lr_scheduler": skillopt.lr_scheduler,
        "lr_control_mode": skillopt.lr_control_mode,
        "skill_update_mode": skillopt.skill_update_mode,
        "rewrite_reasoning_effort": skillopt.rewrite_reasoning_effort,
        "rewrite_max_completion_tokens": skillopt.rewrite_max_completion_tokens,
        "use_slow_update": skillopt.use_slow_update,
        "slow_update_samples": skillopt.slow_update_samples,
        "slow_update_gate_with_selection": skillopt.slow_update_gate_with_selection,
        "longitudinal_pair_policy": skillopt.longitudinal_pair_policy,
        "use_meta_skill": skillopt.use_meta_skill,
        "use_skill_aware_reflection": skillopt.use_skill_aware_reflection,
        "skill_aware_appendix_source": skillopt.skill_aware_appendix_source,
        "skill_aware_consolidate_threshold": (
            skillopt.skill_aware_consolidate_threshold
        ),
        "use_gate": skillopt.use_gate,
        "gate_metric": skillopt.gate_metric,
        "gate_mixed_weight": skillopt.gate_mixed_weight,
        "use_semantic_density": skillopt.use_semantic_density,
        "semantic_density_weight": skillopt.semantic_density_weight,
        "leading_words": None,
        "sel_env_num": validation_size,
        "test_env_num": 0,
        "eval_test": False,
        "workers": cfg.workers,
        "max_api_workers": cfg.workers,
        "codex_trace_to_optimizer": False,
    }


def _smoke_config(cfg: RunCfg) -> RunCfg:
    skillopt = cfg.skillopt.model_copy(
        update={
            "num_epochs": 1,
            "batch_size": 4,
            "reflection_minibatch_size": 2,
            "merge_batch_size": 2,
            "analyst_workers": 2,
            "edit_budget": 2,
            "min_edit_budget": 1,
            "use_slow_update": False,
            "use_meta_skill": False,
        }
    )
    optimization = cfg.optimization.model_copy(
        update={"train_count": 4, "validation_count": 2}
    )
    return cfg.model_copy(
        update={"workers": 2, "skillopt": skillopt, "optimization": optimization}
    )


def preflight_optimizer(
    cfg: RunCfg, *, track_with_mlflow: bool = False
) -> dict[str, Any]:
    """Verify the exact traced optimizer request without starting training."""
    if not track_with_mlflow:
        with optimizer_request_context(cfg):
            return run_optimizer_preflight(cfg)

    setup_tracking(cfg.tracking)
    mlflow.openai.autolog(exclusive=False, log_traces=True)
    with mlflow.start_run(
        run_name=f"skillopt-preflight-{datetime.now(UTC):%Y-%m-%d_%H-%M-%S_%f}"
    ) as run:
        mlflow.log_params(
            {
                "optimizer_model": cfg.optimizer_model.model,
                "optimizer_thinking": cfg.skillopt.optimizer.thinking,
                "optimizer_reasoning_effort": (
                    cfg.skillopt.optimizer.reasoning_effort
                ),
            }
        )
        with optimizer_request_context(cfg):
            result = run_optimizer_preflight(cfg)
        mlflow.log_metrics(
            {
                "reasoning_characters": result["reasoning_characters"],
                "response_characters": result["response_characters"],
            }
        )
        return {"mlflow_run_id": run.info.run_id, **result}


def run_induction(
    cfg: RunCfg,
    *,
    task_groups: list[str] | None = None,
    track_with_mlflow: bool = False,
    expected_task_ids: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    condition = ("per_cluster_taxoskill" if cfg.optimization.cluster_id is not None else
                 "global_taxoskill" if cfg.optimization.train_selection == "cluster" else "global_random")
    local_run_id = canonical_run_name(condition, cfg.seed)
    if cfg.skillopt.resume_run_id not in (None, local_run_id):
        raise ValueError(f"resume run must be {local_run_id!r} for this condition and seed")
    run_dir = skillopt_root(cfg.env.name, cfg.seed, omission=cfg.omission) / local_run_id
    if cfg.optimization.cluster_id is not None:
        run_dir /= f"cluster_{cfg.optimization.cluster_id}"
    run_dir = run_dir.resolve()
    if cfg.skillopt.resume_run_id is not None and not run_dir.is_dir():
        raise FileNotFoundError(f"SkillOpt resume output does not exist: {run_dir}")
    if cfg.skillopt.resume_run_id is None and run_dir.exists():
        raise FileExistsError(f"SkillOpt output already exists: {run_dir}")
    if cfg.skillopt.resume_run_id is not None:
        validate_artifact_scope(run_dir, environment=cfg.env.name, seed=cfg.seed, omission=cfg.omission)
    if cfg.skillopt.initial_skill_file is not None:
        validate_artifact_scope(Path(cfg.skillopt.initial_skill_file).parent,
                                environment=cfg.env.name, seed=cfg.seed, omission=cfg.omission)
    candidate_pool_path = cfg.optimization.candidate_pool_file
    candidate_pool = None
    if cfg.omission is not None and candidate_pool_path is None:
        raise ValueError("condition-scoped training requires optimization.candidate_pool_file")
    if cfg.omission is not None and cfg.optimization.selection_lock_file is None:
        raise ValueError('Controlled-pool training requires a pinned selection lock')
    if candidate_pool_path is not None:
        candidate_pool = load_candidate_pool(Path(candidate_pool_path), environment=cfg.env.name,
                                             seed=cfg.seed, omission=cfg.omission)
        if cfg.skillopt.resume_run_id is not None:
            saved_pool = run_dir / 'candidate_pool.json'
            if not saved_pool.is_file() or type(candidate_pool).model_validate_json(saved_pool.read_text()) != candidate_pool:
                raise ValueError('resume candidate pool differs from the saved training pool')

    environment = adapter_for_environment(cfg.env.name)
    environment.validate_react_config(cfg.react)
    probe = environment.make_env(cfg.env)
    try:
        splits, _ = resolve_optimization_data(
            optimization_cfg=cfg.optimization,
            env_cfg=cfg.env,
            seed=cfg.seed,
            adapter=environment,
            probe=probe,
            task_groups=task_groups,
            omission=cfg.omission,
        )
        if expected_task_ids is not None:
            actual_task_ids = {
                "train": [task.key.canonical for task in splits.train],
                "validation": [task.key.canonical for task in splits.validation],
            }
            if actual_task_ids != expected_task_ids:
                raise ValueError("resolved training/validation IDs differ from locked selections")
        evaluation_task_ids = environment.evaluation_task_ids(
            probe, cfg.evaluation.test_sets
        )
        train_records, validation_records = selected_task_records(probe, splits)
        development_records = {
            "development": probe.task_records("development")  # type: ignore[attr-defined]
        }
    finally:
        probe.close()

    cfg = _capacity_aware_percluster_config(cfg, train_size=len(train_records))

    if track_with_mlflow:
        setup_tracking(cfg.tracking)
        mlflow.openai.autolog(exclusive=False, log_traces=True)
        run_context = mlflow.start_run(run_name=local_run_id)
    else:
        run_context = nullcontext(local_run_id)

    with run_context as run_handle:
        run_id = local_run_id
        if cfg.skillopt.initial_skill_file is None:
            initial_skill = environment.initial_skill()
        else:
            seed_path = Path(cfg.skillopt.initial_skill_file).resolve(strict=True)
            initial_skill = seed_path.read_text(encoding="utf-8")
            if not initial_skill.strip():
                raise ValueError(f"initial skill file is empty: {seed_path}")
        if cfg.skillopt.resume_run_id is None:
            run_dir.mkdir(parents=True)
            initial_skill_path = run_dir / "initial_skill.md"
            initial_skill_path.write_text(initial_skill, encoding="utf-8")
        else:
            initial_skill_path = run_dir / "initial_skill.md"
            if not initial_skill_path.is_file():
                raise FileNotFoundError(
                    f"SkillOpt resume has no initial skill artifact: {initial_skill_path}"
                )
            if initial_skill_path.read_text(encoding="utf-8") != initial_skill:
                raise ValueError("SkillOpt resume initial skill differs from the configured seed")

        configure_skillopt_backend(cfg)

        partition_path = cfg.optimization.partition_artifact
        partition_hash = (
            None if partition_path is None else sha256_file(Path(partition_path))
        )
        resolved_config = cfg.model_dump(mode="json")
        if candidate_pool is not None:
            (run_dir / 'candidate_pool.json').write_text(candidate_pool.model_dump_json(indent=2) + '\n')
        selected_tasks = {
            "train": [task.key.canonical for task in splits.train],
            "validation": [task.key.canonical for task in splits.validation],
            "evaluation": {
                test_set: [f"{test_set}:{task_id}" for task_id in task_ids]
                for test_set, task_ids in evaluation_task_ids.items()
            },
        }
        partition_metadata = {"path": partition_path, "sha256": partition_hash}
        for filename, payload in (
            ("resolved_config.json", resolved_config),
            ("selected_tasks.json", selected_tasks),
            ("partition.json", partition_metadata),
        ):
            (run_dir / filename).write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
            if track_with_mlflow:
                mlflow.log_dict(payload, filename)
        run_params = {
            "environment": cfg.env.name,
            "seed": cfg.seed,
            "omission": cfg.omission,
            "workers": cfg.workers,
            "train_count": len(train_records),
            "validation_count": len(validation_records),
            "train_selection": cfg.optimization.train_selection,
            "validation_selection": cfg.optimization.validation_selection,
            "num_epochs": cfg.skillopt.num_epochs,
            "batch_size": cfg.skillopt.batch_size,
        }
        if partition_path is not None:
            if partition_hash is None:
                raise RuntimeError("partition hash was not computed")
            run_params["partition_path"] = partition_path
            run_params["partition_sha256"] = partition_hash
        if track_with_mlflow:
            mlflow.log_params(run_params)

        with optimizer_request_context(cfg):
            preflight = run_optimizer_preflight(cfg)
            if track_with_mlflow:
                mlflow.log_metrics(
                    {
                        "optimizer_preflight_reasoning_characters": preflight[
                            "reasoning_characters"
                        ],
                        "optimizer_preflight_response_characters": preflight[
                            "response_characters"
                        ],
                    }
                )

            dataloader = SelectedTaskDataLoader(train_records, validation_records)
            adapter = ReActSkillOptAdapter(
                dataloader=dataloader,
                env_factory=lambda train_rollout: environment.make_env(
                    cfg.env, task_records=development_records, train_rollout=train_rollout
                ),
                environment_adapter=environment,
                actor=actor_model(cfg),
                react_cfg=cfg.react,
                rollout_workers=cfg.workers,
            )
            summary = ReflACTTrainer(
                _trainer_config(
                    cfg,
                    run_dir=run_dir,
                    validation_size=len(validation_records),
                    initial_skill_path=initial_skill_path,
                ),
                adapter,
            ).train()

        best_skill_path = run_dir / "best_skill.md"
        if not best_skill_path.is_file():
            raise FileNotFoundError("official SkillOpt run produced no best_skill.md")
        best_score = summary["best_selection_hard"]
        if isinstance(best_score, bool) or not isinstance(best_score, (int, float)):
            raise ValueError("official SkillOpt summary has no best_selection_hard")

        artifact = SkillOptArtifact(
            schema_version=3,
            environment=cfg.env.name,
            artifact_kind="global_procedural_memory",
            candidate=best_skill_path.read_text(),
            best_validation_score=float(best_score),
            train_task_ids=[task.key.task_idx for task in splits.train],
            validation_task_ids=[task.key.task_idx for task in splits.validation],
            evaluation_task_ids=evaluation_task_ids,
            train_selection=cfg.optimization.train_selection,
            validation_selection=cfg.optimization.validation_selection,
            partition_artifact=cfg.optimization.partition_artifact,
        )
        artifact_text = artifact.model_dump_json(indent=2)
        (run_dir / "skillopt_artifact.json").write_text(artifact_text)

        history_path = run_dir / "history.json"
        if not history_path.is_file():
            raise FileNotFoundError("official SkillOpt run produced no history.json")
        if track_with_mlflow:
            mlflow.log_metric("best_validation_score", float(best_score))
            mlflow.log_text(artifact_text, "skillopt_artifact.json")
            mlflow.log_artifact(best_skill_path)
            mlflow.log_artifact(history_path)
            for patches_dir in sorted((run_dir / "steps").glob("**/patches")):
                relative_parent = patches_dir.relative_to(run_dir / "steps").parent
                mlflow.log_artifacts(
                    patches_dir,
                    artifact_path=f"skillopt/patches/{relative_parent.as_posix()}",
                )

        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "artifact": artifact.model_dump(),
            "summary": summary,
        }


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--task-groups")
    parser.add_argument("--cluster", type=int, default=None,
                        help="train ONE skill for this discovered cluster (per-cluster skills)")
    parser.add_argument("--resume-run-id")
    parser.add_argument("--mlflow", action="store_true", help="opt in to MLflow tracking")
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument("--smoke", action="store_true")
    profiles.add_argument("--optimizer-preflight", action="store_true")
    parser.add_argument("overrides", nargs="*")
    args = parser.parse_args()

    cfg = load_config(args.config, args.overrides)
    if args.cluster is not None:
        if cfg.optimization.partition_artifact is None:
            raise ValueError("--cluster requires a partition artifact (cluster selection)")
        # Slice one cluster from the shared full-pool selection and group its output by environment.
        cfg = cfg.model_copy(
            update={
                "optimization": cfg.optimization.model_copy(
                    update={"cluster_id": args.cluster}
                ),
                # the folder now carries the cluster id; keep the base run name clean
                "tracking": cfg.tracking.model_copy(update={"run_name": cfg.tracking.run_name}),
            }
        )
        print(
            f"[per-cluster] learning skill for cluster {args.cluster}, "
            f"output -> {skillopt_root(cfg.env.name, cfg.seed, omission=cfg.omission) / canonical_run_name('per_cluster_taxoskill', cfg.seed) / f'cluster_{args.cluster}'}"
        )
    if args.smoke:
        cfg = _smoke_config(cfg)
    if args.resume_run_id is not None:
        configured = cfg.skillopt.resume_run_id
        if configured is not None and configured != args.resume_run_id:
            raise ValueError(
                "--resume-run-id conflicts with skillopt.resume_run_id"
            )
        cfg = cfg.model_copy(
            update={
                "skillopt": cfg.skillopt.model_copy(
                    update={"resume_run_id": args.resume_run_id}
                )
            }
        )
    if args.optimizer_preflight:
        result = preflight_optimizer(cfg, track_with_mlflow=args.mlflow)
        destination = (
            f" -> MLflow run {result['mlflow_run_id']}"
            if "mlflow_run_id" in result
            else ""
        )
        print(
            f"[skillopt] optimizer preflight passed{destination} · "
            f"reasoning characters={result['reasoning_characters']}"
        )
        return
    task_groups = (
        None
        if args.task_groups is None
        else [group.strip() for group in args.task_groups.split(",") if group.strip()]
    )
    if args.task_groups is not None and not task_groups:
        raise ValueError("--task-groups must contain at least one task group")
    result = run_induction(
        cfg,
        task_groups=task_groups,
        track_with_mlflow=args.mlflow,
    )
    print(
        f"[skillopt] done -> run {result['run_id']} · "
        f"best validation={result['artifact']['best_validation_score']:.4f}"
    )


if __name__ == "__main__":
    main()
