"""One metadata/schema-driven actor prompt for every environment."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from taxoskill.environment import AgentContext


def _cut(observation: str, limit: int) -> str:
    if len(observation) <= limit:
        return observation
    return f"{observation[:limit]} [... {len(observation) - limit} more characters cut]"


def render_action(action: Any) -> str:
    """Render a past tool call. Multi-line string arguments (a submitted script) are shown
    verbatim in a fenced block so the model reads its own code as code, not as an escaped JSON
    string; everything else stays compact JSON."""
    if not isinstance(action, dict) or "name" not in action or "arguments" not in action:
        return json.dumps(action, ensure_ascii=False, sort_keys=True)
    arguments = action["arguments"]
    if not isinstance(arguments, dict):
        return json.dumps(action, ensure_ascii=False, sort_keys=True)
    blocks = {k: v for k, v in arguments.items() if isinstance(v, str) and "\n" in v}
    if not blocks:
        # Unchanged rendering for every action without a multi-line argument.
        return json.dumps(action, ensure_ascii=False, sort_keys=True)
    inline = {k: v for k, v in arguments.items() if k not in blocks}
    text = str(action["name"])
    if inline:
        text += " " + json.dumps(inline, ensure_ascii=False, sort_keys=True)
    for key in sorted(blocks):
        text += f"\n{key}:\n```\n{blocks[key]}\n```"
    return text


def render_trajectory(
    turns: list[dict[str, Any]], history_observation_chars: int, initial_observation: str
) -> str:
    """Render the episode so far: the initial observation as step 0 (the task's own input, shown
    in full), then every past step. The latest observation is shown in full; earlier ones are cut."""
    last = len(turns)
    return "\n".join(
        [f"Step 0 observation: {initial_observation}"]
        + [
            f"Step {index} reasoning: {turn['reasoning']}\n"
            f"Step {index} action: {render_action(turn['action'])}\n"
            "Observation: "
            + (
                turn["observation"]
                if index == last
                else _cut(turn["observation"], history_observation_chars)
            )
            for index, turn in enumerate(turns, start=1)
        ]
    )


def build_actor_messages(
    *,
    context: AgentContext,
    task: str,
    trajectory: list[dict[str, Any]],
    current_observation: str,
    admissible_actions: list[str] | None,
    procedural_memory: str,
    history_observation_chars: int,
    initial_observation: str,
) -> tuple[str, str]:
    """Return the (system, user) prompt pair for one actor step. ``initial_observation`` is the
    episode's step-0 observation; it stays in every later prompt because in some environments it
    is the task input and cannot be re-observed."""
    system_sections = [
        "You are an agent operating in the environment described below.",
        f"Environment:\n{context.metadata['description']}",
    ]
    system_sections.append(
        "Call exactly one available environment tool for the next action. "
        "Do not return an action as prose or call multiple tools."
    )
    system = "\n\n".join(system_sections)
    sections = [f"Task:\n{task}"]
    if procedural_memory.strip():
        sections.append(f"Procedural memory:\n{procedural_memory}")
    if trajectory:
        sections.append(
            "Interaction so far:\n"
            + render_trajectory(trajectory, history_observation_chars, initial_observation)
        )
    else:
        sections.append(f"Current observation:\n{current_observation}")
    if admissible_actions is not None:
        actions = [action for action in admissible_actions if action != "help"]
        if not actions:
            raise ValueError("environment returned no usable admissible actions")
        sections.append(
            "Currently admissible actions:\n"
            + "\n".join(f"- {action}" for action in actions)
        )
    return system, "\n\n".join(sections)


def prompt_hashes(context: AgentContext) -> dict[str, str]:
    context_payload = json.dumps(
        {
            "metadata": context.metadata,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in context.tools
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    composer = "environment+native_tools+task+memory+trajectory(step0-initial,cut-history,block-args)+observation+admissible"
    return {
        "agent_context": hashlib.sha256(context_payload.encode("utf-8")).hexdigest(),
        "generic_prompt_composer": hashlib.sha256(composer.encode("utf-8")).hexdigest(),
    }
