"""TnT-LLM-style task taxonomy: LLM generates task types from raw tasks, then labels every task.

Wan et al. (KDD 2024) "TnT-LLM": (1) taxonomy generation over batches of raw items; (2) preliminary
assignment of every item; (3) one assignment-aware review using cluster examples and counts; and
(4) final reassignment. Nothing is summarized or embedded; raw task instructions are the only
dataset input. Dataset-agnostic: the prompts contain no domain words.

    python -m taxoskill.optimization.partitioning.taxonomy \
        --config configs/experiments/sciworld/base.yaml

Outputs (cached, resumable) in outputs/partitions/taxonomy/<env>/:
    taxonomy.json   the task types (name + definition) after every generation/update step
    labels.json     one generated taxonomy label per development task
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import random

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from taxoskill.config import RunCfg, SubModelCfg, load_config
from taxoskill.llm import Model
from taxoskill.openenv import make_openenv
from taxoskill.task_files import TaskPool, load_manifest
from taxoskill.optimization.partitioning.source import load_endpoint_pool
from taxoskill.optimization.partitioning.taxonomy_prompts import (
    ASSIGN_TASKS_PROMPT,
    GENERATE_TAXONOMY_PROMPT,
    REVIEW_ASSIGNMENTS_PROMPT,
    UPDATE_TAXONOMY_PROMPT,
)

OUT = Path("outputs/partitions/taxonomy")
GENERATION_MODEL = "deepseek-v4-pro"
GENERATION_THINKING = True
GENERATION_EFFORT = "high"
GENERATION_MAX_TOKENS = 32000
ASSIGNMENT_MODEL = "deepseek-v4-flash"
STABLE_NAME_BATCHES = 5
SCIENCEWORLD_STABLE_NAME_BATCHES = 5


def _chat(
    model: str,
    thinking: bool,
    effort: Literal["high", "max"],
    max_tokens: int,
) -> Model:
    cfg = load_config(Path("config.yaml"), [])
    if model == ASSIGNMENT_MODEL:
        profile = cfg.actor_model
    elif model == GENERATION_MODEL:
        profile = cfg.optimizer_model
    else:
        profile = cfg.optimizer_model.model_copy(update={"model": model})
    policy = SubModelCfg(
        thinking=thinking,
        temperature=0.0,
        max_tokens=max_tokens,
        reasoning_effort=effort,
    )
    runtime = cfg.model.model_copy(update={"timeout": 600, "max_retries": 2})
    return Model(profile, policy, runtime)


def _json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"no JSON object in model response: {text[:300]!r}")
    return json.loads(text[start : end + 1])


def _invoke_json(llm: Model, prompt: str, *, attempts: int = 3) -> dict:
    """Call the model and parse its JSON; an empty body (transient API failure) is retried."""
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _json(llm.chat("You are a careful taxonomy analyst.", prompt))
        except (RuntimeError, ValueError, json.JSONDecodeError) as error:
            if isinstance(error, RuntimeError) and "empty response" not in str(error):
                raise
            last = error
            print(
                f"[taxonomy] unusable response (attempt {attempt}/{attempts}): "
                f"{type(error).__name__}: {str(error)[:120]}; retrying",
                flush=True,
            )
    raise RuntimeError(f"model returned unusable responses {attempts} times") from last


def _fmt_tasks(pool: TaskPool, idxs: list[int]) -> str:
    return "\n".join(f"[{pool.task_ids[i]}] {' '.join(pool.instructions[i].split())}" for i in idxs)


def _fmt_taxonomy(types: list[dict]) -> str:
    return "\n".join(f"- {t['name']}: {t['definition']}" for t in types)


def render_environment(env: str, *, cfg: RunCfg | None = None) -> str:
    """Render the label-free action interface of an environment into a prompt block."""
    if cfg is None:
        cfg = load_config(Path("configs/experiments") / env / "base.yaml", [])
    endpoint = make_openenv(cfg.env)
    try:
        ctx = endpoint.agent_context()
        metadata = dict(ctx.metadata)
        description = str(metadata.get("description", "")).strip()
        tools = list(ctx.tools) if getattr(ctx, "tools", None) else []
    finally:
        endpoint.close()

    parts: list[str] = []
    if description:
        parts.append(description)
    if tools:
        rows = []
        for tool in tools:
            props = tool.input_schema.get("properties", {})
            fields = [
                f"{name}({'required' if name in tool.input_schema.get('required', []) else 'optional'})"
                for name in props
            ]
            suffix = f"  [{', '.join(fields)}]" if fields else ""
            rows.append(f"- {tool.name}: {tool.description}{suffix}")
        parts.append("AVAILABLE ACTIONS:\n" + "\n".join(rows))
    return "\n\nThe agent acts in the following environment:\n" + "\n\n".join(parts)


def generation_prompt(tasks: str, environment: str) -> str:
    """Build the initial instruction-only taxonomy prompt."""
    return GENERATE_TAXONOMY_PROMPT.format(tasks=tasks, environment=environment)


def update_prompt(tasks: str, types: list[dict], environment: str) -> str:
    """Build the taxonomy-update prompt for a new task batch."""
    return UPDATE_TAXONOMY_PROMPT.format(
        taxonomy=_fmt_taxonomy(types),
        tasks=tasks,
        environment=environment,
    )


def assignment_prompt(tasks: str, types: list[dict], environment: str) -> str:
    """Build the instruction-only assignment prompt."""
    return ASSIGN_TASKS_PROMPT.format(
        taxonomy=_fmt_taxonomy(types), tasks=tasks, environment=environment
    )


def _representative_ids(ids: list[str], limit: int) -> list[str]:
    if limit <= 0:
        return []
    if len(ids) <= limit:
        return ids
    if limit == 1:
        return ids[:1]
    return [ids[round(index * (len(ids) - 1) / (limit - 1))] for index in range(limit)]


def _review_example_counts(sizes: dict[str, int], budget: int) -> dict[str, int]:
    """Allocate a total review budget equally, redistributing small-type shortfalls."""
    if budget < 1:
        raise ValueError("assignment review example budget must be positive")
    counts = dict.fromkeys(sizes, 0)
    remaining = min(budget, sum(sizes.values()))
    while remaining:
        for name, size in sizes.items():
            if counts[name] < size:
                counts[name] += 1
                remaining -= 1
                if not remaining:
                    break
    return counts


def assignment_review_prompt(
    pool: TaskPool,
    types: list[dict],
    labels: dict[str, str],
    *,
    example_budget: int,
    environment: str,
) -> str:
    """Build a development-only audit prompt from preliminary assignments."""

    if set(labels) != set(pool.task_ids):
        raise ValueError("assignment review labels do not match the development pool")
    instructions = dict(zip(pool.task_ids, pool.instructions, strict=True))
    assigned: dict[str, list[str]] = defaultdict(list)
    for task_id in pool.task_ids:
        assigned[labels[task_id]].append(task_id)
    counts = _review_example_counts(
        {task_type["name"]: len(assigned.get(task_type["name"], [])) for task_type in types},
        example_budget,
    )
    sections: list[str] = []
    for task_type in types:
        name = task_type["name"]
        ids = assigned.get(name, [])
        examples = "\n".join(
            f"  [{task_id}] {' '.join(instructions[task_id].split())}"
            for task_id in _representative_ids(ids, counts[name])
        ) or ("  (no assigned tasks)" if not ids else "  (no examples allocated)")
        sections.append(
            f"TYPE: {name}\nDEFINITION: {task_type['definition']}\n"
            f"ASSIGNED DEVELOPMENT COUNT: {len(ids)}\nEXAMPLES:\n{examples}"
        )
    return REVIEW_ASSIGNMENTS_PROMPT.format(
        task_count=len(pool),
        environment=environment,
        audit="\n\n".join(sections),
    )


def refine_taxonomy_from_assignments(
    pool: TaskPool,
    types: list[dict],
    labels: dict[str, str],
    *,
    out: Path,
    example_budget: int = 150,
    environment: str = "",
) -> list[dict]:
    """Run one cached assignment-aware development-only taxonomy review."""
    prompt = assignment_review_prompt(
        pool,
        types,
        labels,
        example_budget=example_budget,
        environment=environment,
    )
    type_fingerprint = hashlib.sha256(
        json.dumps(types, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    label_fingerprint = hashlib.sha256(
        json.dumps(
            [(task_id, labels[task_id]) for task_id in pool.task_ids],
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    config = {
        "model": GENERATION_MODEL,
        "thinking": GENERATION_THINKING,
        "reasoning_effort": GENERATION_EFFORT,
        "max_tokens": GENERATION_MAX_TOKENS,
        "example_budget": example_budget,
        "example_allocation": "uniform across types, capped by size, redistribute shortfalls",
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "source_types_sha256": type_fingerprint,
        "source_labels_sha256": label_fingerprint,
    }
    log = out / "taxonomy.json"
    cached = json.loads(log.read_text())
    refinement = cached.get("assignment_refinement")
    if isinstance(refinement, dict) and refinement.get("config") == config:
        return _validate_types(refinement["task_types"])

    llm = _chat(
        GENERATION_MODEL,
        GENERATION_THINKING,
        GENERATION_EFFORT,
        GENERATION_MAX_TOKENS,
    )
    response = _invoke_json(llm, prompt)
    refined = _validate_types(response["task_types"])
    sizes = Counter(labels.values())
    cached["schema_version"] = 5
    cached["assignment_refinement"] = {
        "config": config,
        "source_cluster_sizes": dict(sorted(sizes.items())),
        "task_types": refined,
        "decisions": response.get("decisions", []),
    }
    cached["history"] = [
        item for item in cached["history"] if item.get("step") != "assignment_review_001"
    ]
    cached["history"].append({
        "step": "assignment_review_001",
        "task_types": refined,
        "decisions": response.get("decisions", []),
    })
    log.write_text(json.dumps(cached, indent=2) + "\n")
    print(
        f"[taxonomy] assignment review: {len(types)} -> {len(refined)} types",
        flush=True,
    )
    return refined


def taxonomy_input_fingerprint(task_ids: list[str], instructions: list[str]) -> str:
    if len(task_ids) != len(instructions):
        raise ValueError("task ids and taxonomy instructions must align")
    payload = json.dumps(
        list(zip(task_ids, instructions, strict=True)),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def taxonomy_generation_config(*, batch: int, seed: int, env: str = "") -> dict:
    prompt_sha256 = hashlib.sha256(
        "\n".join(
            (
                GENERATE_TAXONOMY_PROMPT,
                UPDATE_TAXONOMY_PROMPT,
            )
        ).encode("utf-8")
    ).hexdigest()
    return {
        "batch": batch,
        "seed": seed,
        "stable_name_batches": (
            SCIENCEWORLD_STABLE_NAME_BATCHES if env in {"sciworld", "scienceworld"}
            else STABLE_NAME_BATCHES
        ),
        "model": GENERATION_MODEL,
        "thinking": GENERATION_THINKING,
        "reasoning_effort": GENERATION_EFFORT,
        "max_tokens": GENERATION_MAX_TOKENS,
        "prompt_sha256": prompt_sha256,
    }


def _validate_types(types: object) -> list[dict]:
    if not isinstance(types, list) or not types:
        raise ValueError("taxonomy must be a non-empty list")
    names = [t["name"].strip() for t in types]
    if len(set(n.casefold() for n in names)) != len(names):
        raise ValueError(f"duplicate task type names: {names}")
    return [{"name": t["name"].strip(), "definition": t["definition"].strip()} for t in types]


def build_taxonomy(
    pool: TaskPool, *, batch: int, seed: int, out: Path, environment: str = ""
) -> list[dict]:
    order = list(range(len(pool)))
    random.Random(seed).shuffle(order)
    batches = [order[i : i + batch] for i in range(0, len(order), batch)]
    log = out / "taxonomy.json"
    input_sha256 = taxonomy_input_fingerprint(pool.task_ids, pool.instructions)
    generation_config = taxonomy_generation_config(batch=batch, seed=seed, env=pool.env)
    stable_batches = generation_config["stable_name_batches"]
    if log.is_file():
        cached = json.loads(log.read_text())
        if cached.get("manifest_sha256") != pool.manifest_sha256:
            raise ValueError(
                f"stale taxonomy cache {log}; development manifest changed, rerun with --force"
            )
        if cached.get("input_sha256") != input_sha256:
            raise ValueError(
                f"stale taxonomy cache {log}; task/prompt input changed, rerun with --force"
            )
        if cached.get("generation_config") != generation_config:
            raise ValueError(
                f"stale taxonomy configuration in {log}; rerun with --force"
            )
        history: list[dict] = cached["history"]
        generation_complete = bool(cached.get("generation_complete", False))
    else:
        history = []
        generation_complete = False

    if generation_complete:
        return history[-1]["task_types"]

    llm = _chat(
        GENERATION_MODEL,
        GENERATION_THINKING,
        GENERATION_EFFORT,
        GENERATION_MAX_TOKENS,
    )

    def save() -> None:
        log.write_text(json.dumps({
            "schema_version": 4,
            "input_contract": "task-instructions-only",
            "manifest_sha256": pool.manifest_sha256,
            "input_sha256": input_sha256,
            "generation_complete": generation_complete,
            "generation_config": generation_config,
            "history": history,
        }, indent=2) + "\n")

    types: list[dict] | None = history[-1]["task_types"] if history else None
    done = {h["step"] for h in history}
    for b, idxs in enumerate(batches):
        step = f"batch_{b:03d}"
        if step in done:
            continue
        tasks = _fmt_tasks(pool, idxs)
        prompt = (
            generation_prompt(tasks, environment)
            if types is None
            else update_prompt(tasks, types, environment)
        )
        types = _validate_types(_invoke_json(llm, prompt)["task_types"])
        history.append({"step": step, "task_types": types})
        save()
        print(f"[taxonomy] {step}: {len(types)} types -> " + "; ".join(t["name"] for t in types), flush=True)
        # Converged after the environment-specific number of matching name sets.
        # (definitions keep getting reworded long after the types themselves are settled)
        names = [{t["name"] for t in h["task_types"]} for h in history[-stable_batches:]]
        if len(names) == stable_batches and all(n == names[0] for n in names[1:]):
            print(f"[taxonomy] converged at {step}: {stable_batches} consecutive matching type-name sets; stopping generation", flush=True)
            break
    if types is None:
        raise ValueError("taxonomy generation produced no task types")
    generation_complete = True
    save()
    return history[-1]["task_types"]


def assign(
    pool: TaskPool,
    types: list[dict],
    *,
    batch: int,
    workers: int,
    environment: str = "",
) -> dict[str, str]:
    llm = _chat(ASSIGNMENT_MODEL, False, "high", 8000)
    names = {t["name"] for t in types}
    idx_batches = [list(range(i, min(i + batch, len(pool)))) for i in range(0, len(pool), batch)]

    def run(idxs: list[int]) -> dict[str, str]:
        expected = {pool.task_ids[i] for i in idxs}
        prompt = assignment_prompt(_fmt_tasks(pool, idxs), types, environment)
        failures: list[str] = []
        for attempt in range(3):
            got = _invoke_json(llm, prompt)["assignments"]
            got = {str(k): str(v).strip() for k, v in got.items()}
            missing = expected - set(got)
            unknown = {k: v for k, v in got.items() if v not in names}
            if not missing and not unknown:
                return {k: got[k] for k in expected}
            failures.append(
                f"attempt {attempt + 1}: {len(got)} ids returned, missing {sorted(missing)[:10]}, "
                f"unknown type names {sorted(set(unknown.values()))[:10]}"
            )
            prompt = prompt + (
                f"\n\nYour previous answer was invalid: missing ids {sorted(missing)[:10]}, "
                f"unknown type names {sorted(set(unknown.values()))[:10]}. Use exact type names and cover every id."
            )
        # The fast assigner would not stay inside the taxonomy for this batch; hand it to the
        # generation model once, and say so.
        print(
            f"[assign] batch starting at task {pool.task_ids[idxs[0]]}: escalating to "
            f"{GENERATION_MODEL} after {'; '.join(failures)}",
            flush=True,
        )
        strong = _chat(GENERATION_MODEL, GENERATION_THINKING, GENERATION_EFFORT, GENERATION_MAX_TOKENS)
        got = _invoke_json(strong, assignment_prompt(_fmt_tasks(pool, idxs), types, environment))["assignments"]
        got = {str(k): str(v).strip() for k, v in got.items()}
        missing = expected - set(got)
        unknown = {k: v for k, v in got.items() if v not in names}
        if missing or unknown:
            raise ValueError(
                f"assignment failed for batch starting at task {pool.task_ids[idxs[0]]} even with "
                f"{GENERATION_MODEL}: missing {sorted(missing)[:10]}, unknown {sorted(set(unknown.values()))[:10]}"
            )
        return {k: got[k] for k in expected}

    labels: dict[str, str] = {}
    with ThreadPoolExecutor(workers) as ex:
        for n, part in enumerate(ex.map(run, idx_batches), 1):
            labels.update(part)
            print(f"[assign] {n}/{len(idx_batches)} batches", flush=True)
    return labels


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    ap = argparse.ArgumentParser(description=__doc__)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", type=Path)
    source.add_argument("--manifest", type=Path)
    ap.add_argument("--gen-batch", type=int, default=150)
    ap.add_argument("--assign-batch", type=int, default=40)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--refine-examples", type=int, default=150,
                    help="total review examples, shared uniformly across discovered types")
    ap.add_argument("--assign-only", action="store_true", help="skip generation; use the last cached taxonomy")
    ap.add_argument("--force", action="store_true", help="discard stale taxonomy and regenerate")
    args = ap.parse_args()

    pool = (
        load_endpoint_pool(args.config)
        if args.config is not None
        else load_manifest(args.manifest, require_role="development")
    )
    environment = render_environment(pool.env) if args.config is not None else pool.environment_description
    out = OUT / pool.env
    out.mkdir(parents=True, exist_ok=True)
    if args.force and args.assign_only:
        ap.error("--force and --assign-only cannot be combined")
    if args.force:
        for path in (out / "taxonomy.json", out / "labels.json"):
            path.unlink(missing_ok=True)

    if args.assign_only:
        cached = json.loads((out / "taxonomy.json").read_text())
        if cached.get("manifest_sha256") != pool.manifest_sha256:
            raise ValueError("cached taxonomy manifest differs; regenerate it without --assign-only")
        expected = taxonomy_input_fingerprint(pool.task_ids, pool.instructions)
        if cached.get("input_sha256") != expected:
            raise ValueError("cached taxonomy is stale; regenerate it without --assign-only")
        expected_config = taxonomy_generation_config(batch=args.gen_batch, seed=args.seed, env=pool.env)
        if (
            cached.get("generation_config") != expected_config
            or not cached.get("generation_complete")
            or not cached.get("history")
        ):
            raise ValueError(
                "cached taxonomy is incomplete or uses different generation settings; "
                "regenerate it without --assign-only"
            )
        history = cached["history"]
        refinement = cached.get("assignment_refinement")
        if isinstance(refinement, dict):
            types = _validate_types(refinement["task_types"])
            step = "assignment_review_001"
        else:
            types = _validate_types(history[-1]["task_types"])
            step = history[-1]["step"]
        print(f"[taxonomy] using cached taxonomy from step {step}")
        labels = assign(
            pool,
            types,
            batch=args.assign_batch,
            workers=args.workers,
            environment=environment,
        )
    else:
        preliminary_types = build_taxonomy(
            pool,
            batch=args.gen_batch,
            seed=args.seed,
            out=out,
            environment=environment,
        )
        preliminary_labels = assign(
            pool,
            preliminary_types,
            batch=args.assign_batch,
            workers=args.workers,
            environment=environment,
        )
        types = refine_taxonomy_from_assignments(
            pool,
            preliminary_types,
            preliminary_labels,
            out=out,
            example_budget=args.refine_examples,
            environment=environment,
        )
        labels = assign(
            pool,
            types,
            batch=args.assign_batch,
            workers=args.workers,
            environment=environment,
        )
    print(f"\n[taxonomy] final ({len(types)} types):")
    for t in types:
        print(f"  - {t['name']}: {t['definition']}")

    name_to_id = {t["name"]: i for i, t in enumerate(types)}
    int_labels = [name_to_id[labels[tid]] for tid in pool.task_ids]
    (out / "labels.json").write_text(json.dumps({
        "env": pool.env,
        "method": (
            "tnt-llm taxonomy (generate/update -> preliminary assign -> "
            "assignment-aware review -> assign)"
        ),
        "manifest_sha256": pool.manifest_sha256,
        "input_contract": "task-instructions-only",
        "input_sha256": taxonomy_input_fingerprint(pool.task_ids, pool.instructions),
        "assignment_config": {
            "model": ASSIGNMENT_MODEL,
            "batch": args.assign_batch,
            "workers": args.workers,
        },
        "task_types": types, "labels": dict(zip(pool.task_ids, int_labels)),
        "label_names": labels,
    }, indent=2))
    print(f"[taxonomy] wrote {out}/labels.json")


if __name__ == "__main__":
    main()
