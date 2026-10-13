"""Generic endpoint-driven optimization policy for self-describing OpenEnv servers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from skillopt.prompts import load_prompt

from taxoskill.config import EnvCfg, ReactCfg
from taxoskill.environment import Env
from taxoskill.openenv import make_openenv
from taxoskill.optimization.tasks import OptimizationTask, OptimizationTaskPools, TaskKey


class OptimizationEnvironmentAdapter(Protocol):
    name: str
    shared_development_pool: bool
    train_source_split: str
    validation_source_split: str

    def make_env(
        self,
        cfg: EnvCfg,
        task_records: dict[str, list[dict[str, Any]]] | None = None,
        *,
        train_rollout: bool = False,
    ) -> Env: ...
    def validate_react_config(self, cfg: ReactCfg) -> None: ...
    def optimization_task_pools(
        self, probe: Env, *, task_groups: list[str] | None
    ) -> OptimizationTaskPools: ...
    def evaluation_task_ids(
        self, probe: Env, test_sets: Sequence[str]
    ) -> dict[str, list[int]]: ...
    def asset_hashes(self, probe: Env) -> dict[str, str]: ...
    def environment_description(self, probe: Env) -> str: ...
    def initial_skill(self) -> str: ...
    def analyst_prompts(self) -> tuple[str, str]: ...


class OpenEnvOptimizationAdapter:
    shared_development_pool = True
    train_source_split = "development"
    validation_source_split = "development"

    def __init__(self, name: str) -> None:
        self.name = name

    def make_env(
        self,
        cfg: EnvCfg,
        task_records: dict[str, list[dict[str, Any]]] | None = None,
        *,
        train_rollout: bool = False,
    ) -> Env:
        """``train_rollout`` marks SkillOpt's training-batch rollouts, the only episodes that
        receive ``train_rollout_reset_options`` on top of ``reset_options``."""
        options = (
            {**cfg.reset_options, **cfg.train_rollout_reset_options}
            if train_rollout
            else cfg.reset_options
        )
        return make_openenv(cfg, task_records=task_records, reset_options=options)

    def validate_react_config(self, cfg: ReactCfg) -> None:
        if cfg.max_steps <= 0:
            raise ValueError("react.max_steps must be positive")

    def optimization_task_pools(
        self,
        probe: Env,
        *,
        task_groups: list[str] | None,
    ) -> OptimizationTaskPools:
        records = probe.task_records("development")  # type: ignore[attr-defined]
        selected_groups = None if task_groups is None else set(task_groups)
        tasks = tuple(
            OptimizationTask(
                key=TaskKey("development", int(record["id"])),
                task_type=str(record.get("task_type") or "unspecified"),
                instruction=str(record["instruction"]),
            )
            for record in records
            if selected_groups is None or record.get("task_type") in selected_groups
        )
        if not tasks:
            raise ValueError("OpenEnv development task pool is empty")
        return OptimizationTaskPools(
            train=tasks,
            validation=tasks,
            shared_development_pool=True,
            train_source_split="development",
            validation_source_split="development",
        )

    def evaluation_task_ids(
        self,
        probe: Env,
        test_sets: Sequence[str],
    ) -> dict[str, list[int]]:
        return {
            split: [int(record["id"]) for record in probe.task_records(split)]  # type: ignore[attr-defined]
            for split in test_sets
        }

    def asset_hashes(self, probe: Env) -> dict[str, str]:
        hashes = {}
        for split in probe.list_splits():  # type: ignore[attr-defined]
            if split.get("name") == "development" and split.get("sha256"):
                hashes["development_task_file"] = str(split["sha256"])
        return hashes

    def environment_description(self, probe: Env) -> str:
        return str(probe.agent_context().metadata.get("description", ""))

    def initial_skill(self) -> str:
        return ""

    def analyst_prompts(self) -> tuple[str, str]:
        return load_prompt("analyst_error"), load_prompt("analyst_success")


def adapter_for_environment(environment: str) -> OpenEnvOptimizationAdapter:
    return OpenEnvOptimizationAdapter(environment)
