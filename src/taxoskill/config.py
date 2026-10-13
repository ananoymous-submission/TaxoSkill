"""Typed run configuration with strict YAML inheritance and dotted CLI overrides.

An experiment file may contain one top-level ``extends`` path. The parent is loaded first and the
experiment's mappings are merged over it. Inheritance cycles, malformed YAML, unknown fields, and
missing values fail loudly. CLI values are then applied and the result is validated as ``RunCfg``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Literal["react", "skillopt"]
    # Per-cluster skill routing directory (outputs/skillopt/<env>/seed_<n>/percluster/). When set with
    # name=skillopt, each evaluation task is assigned to a discovered cluster via the taxonomy and
    # receives ONLY that cluster's learned best skill as its procedural memory.
    percluster_skill_dir: str | None = None
    # Precomputed test-task -> taxonomy-cluster mapping. When set, inference validates and loads
    # this artifact instead of calling the taxonomy assignment model online.
    percluster_routing_artifact: str | None = None

    @model_validator(mode="after")
    def validate_percluster(self) -> "AgentCfg":
        if self.percluster_routing_artifact is not None and self.percluster_skill_dir is None:
            raise ValueError(
                "agent.percluster_routing_artifact requires agent.percluster_skill_dir"
            )
        if self.percluster_skill_dir is not None:
            if self.name != "skillopt":
                raise ValueError(
                    "agent.percluster_skill_dir requires agent.name=skillopt"
                )
        return self


class EnvCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    server_base_env: str = Field(min_length=1)
    timeout: int = Field(gt=0)
    # Keyword arguments forwarded verbatim to every OpenEnv reset, for protocol switches an
    # environment resolves per episode. Empty when the environment needs none.
    reset_options: dict[str, Any]
    # Overrides applied on top of reset_options only for SkillOpt's training-batch rollouts;
    # baseline, gate, slow-update and meta rollouts run without them. Empty when unused.
    train_rollout_reset_options: dict[str, Any]


    @property
    def server_base(self) -> str:
        value = os.environ[self.server_base_env]
        if not value.strip():
            raise ValueError(f"{self.server_base_env} must not be empty")
        return value


class EvaluationCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repeat: int | None = Field(default=None, ge=1, strict=True)
    test_sets: list[str] = Field(min_length=1)
    # Comma-separated run IDs whose local solve-rate artifacts are merged before running
    # unfinished tasks. The resumed invocation writes one complete final artifact.
    resume_from: str | None

    @model_validator(mode="after")
    def validate_test_sets(self) -> "EvaluationCfg":
        if len(set(self.test_sets)) != len(self.test_sets):
            raise ValueError("evaluation.test_sets contains duplicates")
        return self


class ModelProfileCfg(BaseModel):
    """Stable model identity and endpoint, loaded from a dedicated YAML file."""

    model_config = ConfigDict(extra="forbid")

    backend: Literal["deepseek", "openai_compatible"]
    model: str = Field(min_length=1)
    base_url: str | None = None
    base_url_env: str | None = None
    api_key_env: str | list[str]
    # How an OpenAI-compatible server toggles reasoning for this model:
    #   enable_thinking: chat_template_kwargs.enable_thinking switch (Qwen)
    #   always_on: thinking cannot be disabled; only reasoning_effort applies (GLM-5.3)
    #   openrouter: OpenRouter's `reasoning` body object carries both the switch and the effort
    # DeepSeek's own API has one documented switch, so its profiles omit the field.
    thinking_control: Literal["enable_thinking", "always_on", "openrouter"] | None = None
    # OpenRouter only: serve this model from exactly one upstream provider, never a fallback,
    # so the actor is reproducible. Required with thinking_control=openrouter.
    provider: str | None = None

    @model_validator(mode="after")
    def validate_thinking_control(self) -> "ModelProfileCfg":
        if self.backend == "openai_compatible" and self.thinking_control is None:
            raise ValueError("openai_compatible model profiles require thinking_control")
        if self.backend == "deepseek" and self.thinking_control is not None:
            raise ValueError("deepseek model profiles must not set thinking_control")
        if self.thinking_control == "openrouter" and not self.provider:
            raise ValueError("openrouter model profiles must pin a provider")
        if self.thinking_control != "openrouter" and self.provider is not None:
            raise ValueError("provider pinning is only supported for openrouter profiles")
        return self

    @model_validator(mode="after")
    def validate_base_url_source(self) -> "ModelProfileCfg":
        if (self.base_url is None) == (self.base_url_env is None):
            raise ValueError("model profile requires exactly one of base_url or base_url_env")
        names = [self.api_key_env] if isinstance(self.api_key_env, str) else self.api_key_env
        if not names or any(not name.strip() for name in names):
            raise ValueError("model profile api_key_env must name at least one environment variable")
        return self

    @property
    def resolved_base_url(self) -> str:
        if self.base_url is not None:
            value = self.base_url
            source = "base_url"
        else:
            if self.base_url_env is None:
                raise RuntimeError("validated model profile has no base URL source")
            value = os.environ[self.base_url_env]
            source = self.base_url_env
        if not value.strip():
            raise ValueError(f"{source} must not be empty")
        return value

    @property
    def resolved_api_key(self) -> str:
        names = [self.api_key_env] if isinstance(self.api_key_env, str) else self.api_key_env
        values = [os.environ[name] for name in names]
        if any(not value.strip() for value in values):
            raise ValueError("model profile API key environment variables must not be empty")
        return ".".join(values)


class SubModelCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thinking: bool  # run-specific policy translated by the configured model backend
    temperature: float
    max_tokens: int = Field(gt=0)
    reasoning_effort: Literal["low", "medium", "high", "max", "xhigh"]


class ModelCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout: int = Field(gt=0)
    max_retries: int = Field(ge=0)
    rollout: SubModelCfg  # the actor


class ReactCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(gt=0)  # single attempt; one reasoning+action decision per step
    # Earlier observations in the prompt are cut to this many characters; the latest observation
    # is always shown in full. Bounds the per-step prompt when tool results are large.
    history_observation_chars: int = Field(gt=0)
    # What happens when the model's tool call fails client-side validation: "feedback" returns the
    # error as the step's observation and continues; "terminate" ends the episode as a failure.
    invalid_call: Literal["feedback", "terminate"]
    # Whether the client adds a required written `reasoning` argument to every tool call.
    reasoning: bool


class SkillOptModelCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thinking: Literal[True]
    reasoning_effort: Literal["high"]
    temperature: float
    max_tokens: int


class SkillOptCfg(BaseModel):
    """Explicit ReflACT configuration passed to the official SkillOpt trainer."""

    model_config = ConfigDict(extra="forbid")

    num_epochs: int = Field(gt=0)
    batch_size: int = Field(gt=0)
    accumulation: int = Field(gt=0)
    reflection_minibatch_size: int = Field(gt=0)
    merge_batch_size: int = Field(ge=2)
    analyst_workers: int = Field(gt=0)
    rewrite_reasoning_effort: Literal["high"]
    rewrite_max_completion_tokens: Literal[64000]
    failure_only: bool
    edit_budget: int = Field(gt=0)
    min_edit_budget: int = Field(gt=0)
    lr_scheduler: Literal["cosine"]
    lr_control_mode: Literal["fixed"]
    skill_update_mode: Literal["patch"]
    use_slow_update: bool
    slow_update_samples: int = Field(gt=0)
    slow_update_gate_with_selection: bool
    longitudinal_pair_policy: Literal["mixed"]
    use_meta_skill: bool
    use_skill_aware_reflection: bool
    skill_aware_appendix_source: Literal["both"]
    skill_aware_consolidate_threshold: Literal[0]
    use_gate: bool
    gate_metric: Literal["hard", "soft", "mixed"]  # soft = graded progress where the environment reports it
    gate_mixed_weight: Literal[0.5]
    use_semantic_density: Literal[False]
    semantic_density_weight: Literal[0.05]
    optimizer: SkillOptModelCfg
    resume_run_id: str | None
    # Start optimization from this skill file instead of the environment's empty initial
    # skill (stage-2 seeding of a per-cluster run from the split global skill).
    initial_skill_file: str | None


class OptimizationCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_pool_file: str | None = None
    selection_lock_file: str | None = None
    selection_lock_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    partition_artifact: str | None
    train_count: int = Field(gt=0)
    validation_count: int = Field(gt=0)
    train_selection: Literal["random", "cluster"]
    validation_selection: Literal["random", "cluster"]
    # Train ONE skill for a single discovered cluster. Selection still runs ONCE over the full
    # partition, identically to global-cluster; this id only slices that shared split afterward.
    # The induced skill is stored under outputs/skillopt/<env>/seed_<n>/percluster/cluster_<id>/.
    cluster_id: int | None = None

    @model_validator(mode="after")
    def validate_partition_requirement(self) -> "OptimizationCfg":
        if (self.selection_lock_file is None) != (self.selection_lock_sha256 is None):
            raise ValueError('selection lock requires both file and pinned SHA-256')
        cluster_aware = self.train_selection == "cluster" or self.validation_selection == "cluster"
        if cluster_aware and self.partition_artifact is None:
            raise ValueError(
                "cluster-aware optimization requires optimization.partition_artifact"
            )
        if not cluster_aware and self.partition_artifact is not None:
            raise ValueError(
                "only discovered-cluster optimization may load a partition artifact"
            )
        if self.cluster_id is not None and not cluster_aware:
            raise ValueError(
                "optimization.cluster_id requires cluster task selection and a partition artifact"
            )
        if self.cluster_id is not None and self.cluster_id < 0:
            raise ValueError("optimization.cluster_id must be non-negative")
        return self


class TrackingCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tracking_uri: str  # MLflow server, e.g. http://127.0.0.1:5001
    experiment: str  # MLflow experiment name
    run_name: str = Field(min_length=1)  # stable condition name; timestamp is appended at runtime


class RunCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(ge=0)
    # Storage namespace only, not an instruction to construct an imbalanced pool.
    omission: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    workers: int = Field(gt=0)
    actor_model: ModelProfileCfg
    optimizer_model: ModelProfileCfg
    agent: AgentCfg
    env: EnvCfg
    evaluation: EvaluationCfg
    model: ModelCfg
    react: ReactCfg
    optimization: OptimizationCfg
    skillopt: SkillOptCfg
    tracking: TrackingCfg


def _apply_override(data: dict[str, Any], dotted: str, raw_value: str) -> None:
    """Set `a.b.c=value` inside the nested dict. Intermediate keys must already exist —
    an override can change values, not invent config sections."""
    keys = dotted.split(".")
    node = data
    for k in keys[:-1]:
        if not isinstance(node, dict) or k not in node:
            raise KeyError(f"Override {dotted!r}: no such config section {k!r}")
        node = node[k]
    if not isinstance(node, dict) or keys[-1] not in node:
        raise KeyError(f"Override {dotted!r}: no such config key {keys[-1]!r}")
    node[keys[-1]] = yaml.safe_load(raw_value)  # YAML-parse for proper types


def _merge_config(base: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge one explicit experiment overlay onto its parent config."""
    merged = dict(base)
    for key, value in child.items():
        parent_value = merged.get(key)
        if key in {"actor_model", "optimizer_model"}:
            merged[key] = value
        elif isinstance(parent_value, dict) and isinstance(value, dict):
            merged[key] = _merge_config(parent_value, value)
        else:
            merged[key] = value
    return merged


def _read_config(path: Path, stack: tuple[Path, ...]) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if resolved in stack:
        chain = " -> ".join(str(item) for item in (*stack, resolved))
        raise ValueError(f"config inheritance cycle: {chain}")
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"config root must be a mapping: {resolved}")
    child = dict(raw)
    parent_reference = child.pop("extends", None)
    for key in ("actor_model", "optimizer_model"):
        reference = child.get(key)
        if reference is None:
            continue
        if not isinstance(reference, str) or not reference.strip():
            raise TypeError(f"{key} must be a non-empty YAML path: {resolved}")
        profile_path = (resolved.parent / reference).resolve(strict=True)
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        if not isinstance(profile, dict):
            raise TypeError(f"model profile must be a mapping: {profile_path}")
        child[key] = profile
    if parent_reference is None:
        return child
    if not isinstance(parent_reference, str) or not parent_reference.strip():
        raise TypeError(f"config extends must be a non-empty path string: {resolved}")
    parent = _read_config(resolved.parent / parent_reference, (*stack, resolved))
    return _merge_config(parent, child)


def load_config(path: Path, overrides: list[str]) -> RunCfg:
    """Compose, override, and strictly validate one run configuration."""
    data = _read_config(path, ())
    for ov in overrides:
        if "=" not in ov:
            raise ValueError(f"Override must be key=value, got: {ov!r}")
        dotted, raw_value = ov.split("=", 1)
        _apply_override(data, dotted, raw_value)
    cfg = RunCfg.model_validate(data)
    # Only artifact paths are templated; model prompts and other strings are untouched.
    for owner, field in ((cfg.agent, "percluster_skill_dir"), (cfg.skillopt, "initial_skill_file")):
        value = getattr(owner, field)
        if value is not None:
            value = value.replace("{seed}", str(cfg.seed))
            setattr(owner, field, value)
    return cfg
