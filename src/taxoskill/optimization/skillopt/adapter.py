"""Environment-neutral bridge from the ReAct worker to official SkillOpt."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from skillopt.datasets import BatchSpec
from skillopt.envs.base import EnvAdapter

from taxoskill.agents.react import episode_status, run_episode
from taxoskill.agents.prompt import build_actor_messages
from taxoskill.concurrency import FailFastThreadPoolExecutor
from taxoskill.config import ReactCfg
from taxoskill.environment import Env
from taxoskill.llm import Model
from taxoskill.optimization.environment import OptimizationEnvironmentAdapter
from taxoskill.optimization.skillopt.dataloader import SelectedTaskDataLoader
from taxoskill.optimization.tasks import OptimizationTaskSplits, SelectedTask


def _conversation(final: dict[str, Any]) -> list[dict[str, Any]]:
    trajectory = final["trajectory"]
    if not trajectory:
        raise ValueError("optimizer rollout produced no trajectory")
    conversation: list[dict[str, Any]] = []
    for index, turn in enumerate(trajectory):
        action = turn["action"]
        reasoning = turn["reasoning"]
        observation = turn["observation"]
        if isinstance(action, dict) and action:
            action_text = json.dumps(action, ensure_ascii=False, sort_keys=True)
        elif isinstance(action, str) and action.strip():
            action_text = action
        else:
            raise ValueError(f"optimizer trajectory step {index} has an empty action")
        if not isinstance(reasoning, str):
            raise ValueError(f"optimizer trajectory step {index} has non-text reasoning")
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(f"optimizer trajectory step {index} has an empty observation")
        conversation.append({
            "step": index,
            "action": action_text,
            "reasoning": reasoning,
            "model_response": turn["raw_response"],
            "env_feedback": observation,
            "reward": float(turn["reward"]),
            "done": bool(turn["done"]),
        })
    return conversation


def selected_task_records(
    probe: Env, splits: OptimizationTaskSplits
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    total = len(splits.train) + len(splits.validation)
    completed = 0

    def build(selected: SelectedTask) -> dict[str, Any]:
        nonlocal completed
        observation = probe.reset(selected.key.task_idx)
        if observation.task_type != selected.task_type:
            raise ValueError(
                f"task {selected.key.canonical} resolved as "
                f"{observation.task_type!r}, expected {selected.task_type!r}"
            )
        record = {
            "id": selected.key.canonical.replace(":", "__"),
            "task_idx": selected.key.task_idx,
            "source_split": selected.key.source_split,
            "task_description": observation.goal,
        }
        completed += 1
        if completed == 1 or completed % 10 == 0 or completed == total:
            print(
                f"[skillopt] loading selected task instructions {completed}/{total}",
                flush=True,
            )
        return record

    return (
        [build(selected) for selected in splits.train],
        [build(selected) for selected in splits.validation],
    )


class ReActSkillOptAdapter(EnvAdapter):
    """Run the same ReAct worker for any registered optimization environment."""

    def __init__(
        self,
        *,
        dataloader: SelectedTaskDataLoader,
        env_factory: Callable[[bool], Env],
        environment_adapter: OptimizationEnvironmentAdapter,
        actor: Model,
        react_cfg: ReactCfg,
        rollout_workers: int,
    ) -> None:
        self.dataloader = dataloader
        self.env_factory = env_factory
        self.environment_adapter = environment_adapter
        self.actor = actor
        self.react_cfg = react_cfg
        self.rollout_workers = rollout_workers

    def setup(self, cfg: dict[str, Any]) -> None:
        super().setup(cfg)
        self.analyst_workers = cfg["analyst_workers"]
        self.failure_only = cfg["failure_only"]
        self.minibatch_size = cfg["minibatch_size"]
        self.edit_budget = cfg["edit_budget"]

    def get_dataloader(self) -> SelectedTaskDataLoader:
        return self.dataloader

    def get_error_minibatch_prompt(self) -> str:
        return self.environment_adapter.analyst_prompts()[0]

    def get_success_minibatch_prompt(self) -> str:
        return self.environment_adapter.analyst_prompts()[1]

    def build_env_from_batch(
        self, batch: BatchSpec, **kwargs: Any
    ) -> list[dict[str, Any]]:
        if not isinstance(batch.payload, list):
            raise TypeError("SkillOpt batch payload must be a list")
        return [dict(item) for item in batch.payload]

    def build_train_env(
        self, batch_size: int, seed: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        return self.build_env_from_batch(
            self.dataloader.build_train_batch(batch_size, seed)
        )

    def build_eval_env(
        self, env_num: int, split: str, seed: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        return self.build_env_from_batch(
            self.dataloader.build_eval_batch(env_num, split, seed)
        )

    def rollout(
        self,
        env_manager: list[dict[str, Any]],
        skill_content: str,
        out_dir: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        prediction_dir = Path(out_dir) / "predictions"
        prediction_dir.mkdir(parents=True, exist_ok=True)
        # SkillOpt's trainer sets use_eval_feedback only for the training-batch rollouts; the
        # baseline, gate, slow-update, and meta rollouts are evaluation-protocol episodes.
        train_rollout = bool(kwargs.get("use_eval_feedback", False))

        def run_one(item: dict[str, Any]) -> dict[str, Any]:
            env = self.env_factory(train_rollout)
            try:
                final = run_episode(
                    env, self.actor, self.react_cfg, skill_content, item["task_idx"]
                )
                extras = final["diagnostics"]
                context = env.agent_context()
            finally:
                env.close()

            task_dir = prediction_dir / item["id"]
            task_dir.mkdir(parents=True, exist_ok=True)
            conversation = _conversation(final)
            if extras.get("verification"):
                conversation.append({"role": "system", "content": extras["verification"]})
            system_prompt, user_prompt = build_actor_messages(
                context=context,
                task=final["goal"],
                trajectory=[],
                current_observation=final["initial_observation"],
                admissible_actions=final["initial_admissible_actions"],
                procedural_memory=skill_content,
                history_observation_chars=self.react_cfg.history_observation_chars,
                initial_observation=final["initial_observation"],
            )
            tool_catalog = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in context.tools
            ]
            analyst_context: dict[str, str] = {
                "target_system_prompt": (
                    system_prompt
                    + "\n\nAvailable native tools:\n"
                    + json.dumps(tool_catalog, indent=2, ensure_ascii=False, sort_keys=True)
                ),
                "target_user_prompt": user_prompt,
            }
            if extras.get("spreadsheet_preview"):
                analyst_context["spreadsheet_preview"] = extras["spreadsheet_preview"]
            for name, text in analyst_context.items():
                (task_dir / f"{name}.txt").write_text(text, encoding="utf-8")
            if extras.get("code"):
                (task_dir / "code.py").write_text(extras["code"], encoding="utf-8")
            (task_dir / "conversation.json").write_text(
                json.dumps(conversation, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            success = bool(final["success"])
            progress = final["progress"]
            # SkillOpt's soft score: graded goal progress when the environment reports it
            # (ScienceWorld: score/100), otherwise identical to the binary outcome.
            if progress is None:
                soft = float(success)
            else:
                if not 0.0 <= progress <= 1.0:
                    raise ValueError(f"task {item['id']} progress {progress} is outside [0, 1]")
                if success and progress < 1.0:
                    raise ValueError(f"task {item['id']} solved but progress {progress} < 1")
                soft = float(progress)
            status = episode_status(final)
            return {
                "id": item["id"],
                "hard": int(success),
                "soft": soft,
                "task_idx": item["task_idx"],
                "task_description": final["goal"],
                "reward": float(final["reward"]),
                "n_turns": int(final["step"]),
                "fail_reason": "" if success else (extras.get("fail_reason") or status),
                "status": status,
                **analyst_context,
            }

        with FailFastThreadPoolExecutor(max_workers=self.rollout_workers) as executor:
            return list(executor.map(run_one, env_manager))

    def get_task_types(self) -> list[str]:
        # Official benchmark classes are post-hoc metadata, not optimizer inputs.
        return []
