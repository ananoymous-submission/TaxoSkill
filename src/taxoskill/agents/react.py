"""Native-tool ReAct worker: reset, then repeat (model step, environment step) until done.

A caller provides the procedural-memory string explicitly: the no-skill baseline passes an
empty string, an optimizer passes its current candidate. Every environment publishes its own
typed tools; the actor emits exactly one native tool call per step. A call that fails
validation consumes a step and is returned to the model as an error observation. Only the
step cap or the environment ends the episode.
"""

from __future__ import annotations

from typing import Any

import mlflow
from mlflow.entities import SpanType

from taxoskill.agents.prompt import build_actor_messages
from taxoskill.config import ReactCfg
from taxoskill.environment import Env
from taxoskill.llm import Model


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{label} must be non-empty")
    return value


def run_episode(
    env: Env,
    model: Model,
    cfg: ReactCfg,
    procedural_memory: str,
    task_idx: int,
) -> dict[str, Any]:
    """Run one task to completion and return its outcome and trajectory."""
    if not isinstance(procedural_memory, str):
        raise TypeError(
            f"procedural_memory must be str, got {type(procedural_memory).__name__}"
        )
    context = env.agent_context()
    if not context.tools:
        raise ValueError("environment exposes no native tools")

    obs = env.reset(task_idx)
    goal = _required_text(obs.goal, f"task {task_idx} goal")
    observation = _required_text(obs.text, f"task {task_idx} initial observation")
    max_steps = obs.step_limit
    if max_steps <= 0:
        raise ValueError(f"task {task_idx} has invalid step limit {max_steps}")
    if max_steps > cfg.max_steps:
        raise ValueError(
            f"task {task_idx} protocol cap {max_steps} exceeds configured safety cap "
            f"{cfg.max_steps}"
        )

    final: dict[str, Any] = {
        "task_idx": task_idx,
        "goal": goal,
        "task_type": obs.task_type,
        "initial_observation": observation,
        "initial_admissible_actions": obs.admissible_actions,
        "max_steps": max_steps,
        "step": 0,
        "trajectory": [],
        "reward": 0.0,
        "done": False,
        "terminated": False,
        "truncated": False,
        "success": False,
        "progress": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "action_failures": [],
    }
    admissible = obs.admissible_actions

    for step in range(1, max_steps + 1):
        system, user = build_actor_messages(
            context=context,
            task=goal,
            trajectory=final["trajectory"],
            current_observation=observation,
            admissible_actions=admissible,
            procedural_memory=procedural_memory,
            history_observation_chars=cfg.history_observation_chars,
            initial_observation=final["initial_observation"],
        )
        call = model.act(system, user, context.tools, with_reasoning=cfg.reasoning)
        final["step"] = step
        final["input_tokens"] += call.input_tokens
        final["output_tokens"] += call.output_tokens

        if call.failure is not None:
            final["action_failures"].append(
                {"step": step, "category": call.failure, "error": call.error}
            )
            if cfg.invalid_call == "terminate":
                # The benchmark protocol treats a malformed response as the end of the episode.
                final["trajectory"].append(
                    {
                        "action": f"invalid_tool_call:{call.failure}",
                        "reasoning": call.reasoning,
                        "raw_response": call.raw_response,
                        "admissible_actions": admissible,
                        "observation": f"Invalid tool call ({call.failure}): {call.error}.",
                        "reward": 0.0,
                        "terminated": True,
                        "truncated": False,
                        "done": True,
                    }
                )
                final["terminated"] = True
                final["done"] = True
                break
            # Fed back to the model as this step's observation, the way a tool runtime returns
            # an error result. The environment state is unchanged.
            observation = (
                f"Invalid tool call ({call.failure}): {call.error}. "
                "The environment did not act. Call exactly one available tool with "
                "arguments that match its schema."
            )
            final["trajectory"].append(
                {
                    "action": f"invalid_tool_call:{call.failure}",
                    "reasoning": call.reasoning,
                    "raw_response": call.raw_response,
                    "admissible_actions": admissible,
                    "observation": observation,
                    "reward": 0.0,
                    "terminated": False,
                    "truncated": False,
                    "done": False,
                }
            )
            continue

        if call.name is None or call.arguments is None:
            raise RuntimeError("model returned neither a tool call nor a failure")
        action = {"name": call.name, "arguments": call.arguments}
        result = env.step_tool(call.name, call.arguments)
        observation = _required_text(
            result.observation.text, f"task {task_idx} step {step} observation"
        )
        final["trajectory"].append(
            {
                "action": action,
                "reasoning": call.reasoning,
                "raw_response": call.raw_response,
                "admissible_actions": admissible,
                "observation": observation,
                "reward": result.reward,
                "terminated": result.terminated,
                "truncated": result.truncated,
                "done": result.done,
            }
        )
        admissible = result.observation.admissible_actions
        final["reward"] = result.reward
        final["done"] = result.done
        final["terminated"] = result.terminated
        final["truncated"] = result.truncated
        final["progress"] = env.progress()
        if result.done:
            final["success"] = env.success()
            break

    final["diagnostics"] = env.diagnostics()
    return final


def episode_status(final: dict[str, Any]) -> str:
    """How the episode ended: success, terminal_failure, environment_truncation, or step_cap."""
    if final["success"]:
        return "success"
    if final["terminated"]:
        return "terminal_failure"
    if final["truncated"]:
        return "environment_truncation"
    if final["step"] >= final["max_steps"]:
        return "step_cap"
    raise ValueError("episode ended without a recognized termination condition")


def run_task(
    env: Env,
    model: Model,
    cfg: ReactCfg,
    procedural_memory: str,
    task_idx: int,
) -> dict[str, Any]:
    """Run one task inside an MLflow task span. Per-call spans come from the OpenAI autolog."""
    with mlflow.start_span(name=f"task-{task_idx}", span_type=SpanType.CHAIN) as span:
        span.set_inputs({"task_idx": task_idx})
        final = run_episode(env, model, cfg, procedural_memory, task_idx)
        span.set_outputs(
            {
                "solved": final["success"],
                "goal": final["goal"],
                "steps": final["step"],
                "trajectory": final["trajectory"],
                "action_failures": final["action_failures"],
            }
        )
    return final
