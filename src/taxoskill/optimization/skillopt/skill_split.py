"""Split a global TaxoSkill into shared plus type-specific inference guidance.

    python -m taxoskill.optimization.skillopt.skill_split \
        --config configs/experiments/alfworld/cluster_cluster.yaml \
        --skill outputs/skillopt/alfworld/seed_0/global_taxoskill_seed_0/best_skill.md

Writes split.json and cluster_<id>.md under
outputs/skillopt/<environment>/seed_<n>/per_cluster_taxoskill_seed_<n>/.
No additional optimization is performed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import jsonschema

from taxoskill.config import RunCfg, SubModelCfg, load_config
from taxoskill.run_storage import seeded_skill_output, skillopt_root, run_name
from taxoskill.run_storage import validate_artifact_scope
from taxoskill.environment import ToolSpec
from taxoskill.llm import Model
from taxoskill.optimization.partitioning.artifact import PartitionArtifact

GENERAL_FIELD = "general_guidance"
TOOL_NAME = "split_skill"


def field_name(task_type_name: str) -> str:
    """Tool parameters must be identifier-like; cluster names may contain spaces or punctuation."""
    slug = re.sub(r"[^a-z0-9]+", "_", task_type_name.lower()).strip("_")
    if not slug:
        raise ValueError(f"cannot derive a field name from task type {task_type_name!r}")
    return slug


def split_tool(partition: PartitionArtifact) -> ToolSpec:
    """One tool: one text field per cluster (described by its definition), then general guidance."""
    names = [field_name(t.name) for t in partition.task_types]
    if len(set(names)) != len(names) or GENERAL_FIELD in names:
        raise ValueError(f"task type names collide as tool fields: {names}")
    properties: dict[str, Any] = {}
    for task_type in partition.task_types:
        properties[field_name(task_type.name)] = {
            "type": "string",
            "description": (
                f"Every rule of the skill that concerns the task type '{task_type.name}': "
                f"{task_type.definition} Include any rule that names this type's activity, "
                "objects, substances, appliances, or outcome, even if phrased generally. A rule "
                "that concerns several types goes into each of their fields. Write one rule per "
                "line as a markdown bullet. Empty only if nothing in the skill concerns this type."
            ),
        }
    properties[GENERAL_FIELD] = {
        "type": "string",
        "description": (
            "Only rules that hold for every task type without naming any activity, object, "
            "substance, appliance, or task: output format, how to search rooms and containers, "
            "when to stop, how to handle errors and ambiguous prompts, how to verify. A rule "
            "that concerns some types but not all belongs in those types' fields, not here. "
            "Write one rule per line as a markdown bullet."
        ),
    }
    return ToolSpec(
        name=TOOL_NAME,
        description=(
            "Reorganize a learned agent skill document into per-task-type sections and general "
            "guidance. Sort the type-specific rules first; general guidance is what applies to "
            "all types. A rule may appear in several type fields. Light editing is allowed: "
            "merge fragments of the same rule, fix grammar, drop exact duplicates, and order "
            "rules sensibly. Do not add advice the skill does not contain and do not drop a "
            "rule."
        ),
        input_schema={
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    )


def split_skill(model: Model, skill: str, partition: PartitionArtifact) -> dict[str, str]:
    """Return {field: text} for the general field, every cluster field, and ``reasoning``."""
    if not skill.strip():
        raise ValueError("cannot split an empty skill")
    tool = split_tool(partition)
    system = (
        "You are organizing a learned skill document for an agent. The document was optimized "
        "over tasks from every task type below. First assign every rule that concerns "
        "particular task types to each of those types' fields; only rules that apply to all "
        "types without naming any activity, object, or appliance go to general guidance. You "
        "may tidy wording and merge fragments, but never invent or drop a rule. Return one "
        "JSON object matching the supplied schema, without markdown fences or other text."
    )
    schema = dict(tool.input_schema)
    schema["properties"] = dict(schema["properties"])
    schema["properties"]["reasoning"] = {
        "type": "string", "minLength": 1,
        "description": "Briefly explain how the existing rules were assigned to sections.",
    }
    schema["required"] = [*schema["required"], "reasoning"]
    user = (tool.description + "\n\nOutput JSON schema:\n" + json.dumps(schema)
            + "\n\nLearned skill document:\n\n" + skill.strip())
    for attempt in range(1, 4):
        response = model.chat(system, user)
        try:
            arguments = json.loads(response)
            jsonschema.validate(arguments, schema)
            if not arguments[GENERAL_FIELD].strip():
                raise ValueError("skill split produced no general guidance")
            break
        except (ValueError, jsonschema.ValidationError) as error:
            detail = error.message if isinstance(error, jsonschema.ValidationError) else str(error)
            print(f"[split] attempt {attempt} failed JSON validation: {detail}", flush=True)
    else:
        raise RuntimeError("skill split failed JSON validation after 3 attempts")
    reasoning = arguments.pop("reasoning")
    by_field = {field_name(t.name): t.name for t in partition.task_types}
    fields: dict[str, str] = {
        str(by_field.get(name, name)): value.strip() for name, value in arguments.items()
    }
    if not fields[GENERAL_FIELD]:
        raise ValueError("skill split produced no general guidance")
    fields = consolidate(fields, [t.name for t in partition.task_types])
    fields["reasoning"] = reasoning
    return fields


def _bullets(text: str) -> list[str]:
    """Split a field into rules: one per top-level bullet, whole text if there are no bullets."""
    rules: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")) or not rules:
            rules.append(stripped.lstrip("-* ").strip())
        else:
            rules[-1] += " " + stripped
    return rules


def _words(rule: str) -> frozenset[str]:
    return frozenset(w for w in re.findall(r"[a-z0-9<>_]+", rule.lower()) if len(w) > 2)


def _same_rule(a: str, b: str, threshold: float = 0.6) -> bool:
    """Two rules are the same rule when their word sets mostly overlap (light rewording)."""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= threshold


def consolidate(fields: dict[str, str], cluster_names: list[str]) -> dict[str, str]:
    """Deterministic cleanup after the model's split.

    A rule the model placed in every cluster field is general by definition and moves to
    general guidance; a rule that restates a general rule is dropped from the cluster fields;
    duplicates inside one field are dropped. Rules are compared by word overlap so lightly
    reworded copies count as the same rule. Nothing is reworded here.
    """
    general = _bullets(fields[GENERAL_FIELD])
    per_cluster = {name: _bullets(fields[name]) for name in cluster_names}

    def in_general(rule: str) -> bool:
        return any(_same_rule(rule, g) for g in general)

    first = cluster_names[0]
    for rule in list(per_cluster[first]):
        if all(any(_same_rule(rule, r) for r in per_cluster[name]) for name in cluster_names[1:]):
            if not in_general(rule):
                general.append(rule)
    for name in cluster_names:
        kept: list[str] = []
        for rule in per_cluster[name]:
            if in_general(rule) or any(_same_rule(rule, k) for k in kept):
                continue
            kept.append(rule)
        per_cluster[name] = kept
    out = dict(fields)
    out[GENERAL_FIELD] = "\n".join(f"- {r}" for r in general)
    for name, rules in per_cluster.items():
        out[name] = "\n".join(f"- {r}" for r in rules)
    return out


def seed_for_cluster(fields: dict[str, str], task_type_name: str) -> str:
    """The initial skill for one cluster: general guidance, then that cluster's own guidance.

    The cluster's name and definition stay out of the skill: the skill is what the agent
    reads, and it should not learn which taxonomy bucket its task fell into.
    """
    parts = ["# General guidance", "", fields[GENERAL_FIELD], "", "# Task-specific guidance", ""]
    section = fields[task_type_name]
    parts.append(section if section else "(none yet)")
    return "\n".join(parts).rstrip() + "\n"


def uncovered_lines(skill: str, fields: dict[str, str]) -> list[str]:
    """Skill lines with no verbatim match in any field (informational; light rewording is allowed)."""
    haystack = "\n".join(text for name, text in fields.items() if name != "reasoning")
    return [
        line for line in (raw.strip() for raw in skill.splitlines())
        if line and line.lstrip("#-*0123456789. ").strip() not in haystack
    ]


def split_policy(cfg: RunCfg) -> SubModelCfg:
    """The optimizer model with reasoning on: sorting rules well needs judgment, not speed."""
    optimizer = cfg.skillopt.optimizer
    return SubModelCfg(
        thinking=True,
        temperature=optimizer.temperature,
        # The split reproduces every rule of the skill across all fields after a reasoning pass;
        # a 4k-word skill exceeded 32k completion tokens, so use the optimizer's own limit.
        max_tokens=optimizer.max_tokens,
        reasoning_effort=optimizer.reasoning_effort,
    )


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True, help="global best_skill.md")
    parser.add_argument("--out", type=Path, help="optional canonical output path; inferred from environment and seed")
    parser.add_argument("--seed", type=int, help="override the configuration seed")
    args = parser.parse_args()

    overrides = [] if args.seed is None else [f"seed={args.seed}"]
    cfg = load_config(args.config, overrides)
    expected_out = skillopt_root(cfg.env.name, cfg.seed, omission=cfg.omission) / run_name("per_cluster_taxoskill", cfg.seed)
    args.out = expected_out if args.out is None else seeded_skill_output(args.out, cfg.env.name, cfg.seed, omission=cfg.omission)
    if args.out != expected_out:
        raise ValueError(f"split output must be {expected_out}")
    if args.out.exists():
        raise FileExistsError(f"split output already exists; refusing to overwrite: {args.out}")
    if cfg.optimization.partition_artifact is None:
        raise ValueError("config must set optimization.partition_artifact")
    partition = PartitionArtifact.model_validate_json(
        Path(cfg.optimization.partition_artifact).read_text(encoding="utf-8")
    )
    if partition.environment != cfg.env.name:
        raise ValueError("partition environment does not match the config")
    validate_artifact_scope(args.skill.parent, environment=cfg.env.name,
                            seed=cfg.seed, omission=cfg.omission)
    skill = args.skill.read_text(encoding="utf-8")

    model = Model(cfg.optimizer_model, split_policy(cfg), cfg.model)
    fields = split_skill(model, skill, partition)

    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "split.json").write_text(
        json.dumps(
            {"source_skill": str(args.skill), "seed": cfg.seed, "omission": cfg.omission,
             "environment": cfg.env.name, "partition_id": partition.partition_id, **fields},
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    for index, task_type in enumerate(partition.task_types):
        seed = seed_for_cluster(fields, task_type.name)
        (args.out / f"cluster_{index}.md").write_text(seed, encoding="utf-8")
        print(f"[split] cluster_{index} ({task_type.name}): {len(fields[task_type.name])} chars")
    print(f"[split] general guidance: {len(fields[GENERAL_FIELD])} chars")
    missing = uncovered_lines(skill, fields)
    if missing:
        print(f"[split] {len(missing)} skill lines not found verbatim in any field:")
        for line in missing[:10]:
            print(f"    {line[:110]}")
    print(f"[split] wrote {args.out}")


if __name__ == "__main__":
    main()
