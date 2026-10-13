"""Small deployment artifact for a SkillOpt-learned procedural memory."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SkillOptArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal[3]
    environment: str = Field(min_length=1)
    artifact_kind: Literal["global_procedural_memory"]
    candidate: str
    best_validation_score: float = Field(ge=0.0, le=1.0)
    train_task_ids: list[int] = Field(min_length=1)
    validation_task_ids: list[int] = Field(min_length=1)
    evaluation_task_ids: dict[str, list[int]] = Field(min_length=1)
    train_selection: Literal["random", "cluster"]
    validation_selection: Literal["random", "cluster"]
    partition_artifact: str | None

    @model_validator(mode="after")
    def validate_evaluation_task_ids(self) -> "SkillOptArtifact":
        for test_set, task_ids in self.evaluation_task_ids.items():
            if not test_set or not task_ids:
                raise ValueError("evaluation task IDs require non-empty test sets and task lists")
            if len(set(task_ids)) != len(task_ids) or any(task_id < 0 for task_id in task_ids):
                raise ValueError(f"invalid evaluation task IDs for {test_set!r}")
        return self
