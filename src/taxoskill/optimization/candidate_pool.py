"""Validated instruction-pool subsets for controlled-imbalance training."""
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from taxoskill.optimization.partitioning.artifact import task_pool_hash, unique_pool_tasks
from taxoskill.optimization.tasks import OptimizationTaskPools, TaskKey


class CandidatePoolManifest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    schema_version: Literal[3]
    environment: str
    omission: float = Field(ge=0, le=1, allow_inf_nan=False)
    achieved_omission: float = Field(ge=0, le=1, allow_inf_nan=False)
    seed: int = Field(ge=0, strict=True)
    source_split: Literal['development']
    full_pool_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    task_ids: list[Annotated[int, Field(ge=0, strict=True)]] = Field(min_length=1)

    @model_validator(mode='after')
    def unique_ids(self):
        if len(self.task_ids) != len(set(self.task_ids)):
            raise ValueError('candidate pool contains duplicate task IDs')
        return self

    def validate_scope(self, *, environment: str, seed: int, omission: float):
        if (self.environment, self.seed, self.omission) != (environment, seed, omission):
            raise ValueError('candidate pool environment/seed/condition differs from configuration')
        return self


def load_candidate_pool(path: Path, *, environment: str, seed: int,
                        omission: float) -> CandidatePoolManifest:
    return CandidatePoolManifest.model_validate_json(path.read_text()).validate_scope(
        environment=environment, seed=seed, omission=omission)


def restrict_candidate_pool(pools: OptimizationTaskPools, manifest: CandidatePoolManifest) -> OptimizationTaskPools:
    """Filter only after the frozen taxonomy was validated against the complete source."""
    if not pools.shared_development_pool or pools.train_source_split != manifest.source_split:
        raise ValueError('candidate pools require a shared development source')
    source = unique_pool_tasks(pools)
    if task_pool_hash(source) != manifest.full_pool_sha256:
        raise ValueError('candidate pool source hash differs from live instructions')
    wanted = {TaskKey(manifest.source_split, i) for i in manifest.task_ids}
    if not wanted <= {task.key for task in source}:
        raise ValueError('candidate pool contains unknown development task IDs')
    selected = tuple(task for task in pools.train if task.key in wanted)
    return OptimizationTaskPools(selected, selected, True,
                                 pools.train_source_split, pools.validation_source_split)
