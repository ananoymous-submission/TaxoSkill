"""Fixed selected-task loader for the official SkillOpt trainer."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any

from skillopt.datasets import BaseDataLoader, BatchSpec


class SelectedTaskDataLoader(BaseDataLoader):
    def __init__(
        self,
        train_records: Sequence[dict[str, Any]],
        validation_records: Sequence[dict[str, Any]],
    ) -> None:
        if not train_records or not validation_records:
            raise ValueError("SkillOpt train and validation records must be non-empty")
        self.train_records = tuple(dict(record) for record in train_records)
        self.validation_records = tuple(dict(record) for record in validation_records)
        train_ids = [record["id"] for record in self.train_records]
        validation_ids = [record["id"] for record in self.validation_records]
        if len(set(train_ids)) != len(train_ids):
            raise ValueError("SkillOpt training records contain duplicate IDs")
        if len(set(validation_ids)) != len(validation_ids):
            raise ValueError("SkillOpt validation records contain duplicate IDs")
        if set(train_ids) & set(validation_ids):
            raise ValueError("SkillOpt train and validation records overlap")

    def get_train_size(self) -> int:
        return len(self.train_records)

    def plan_train_epoch(
        self,
        *,
        epoch: int,
        steps_per_epoch: int,
        accumulation: int,
        batch_size: int,
        seed: int,
        **kwargs: Any,
    ) -> list[BatchSpec]:
        records = [dict(record) for record in self.train_records]
        random.Random(seed + epoch * 1000).shuffle(records)
        batches = [
            records[start : start + batch_size]
            for start in range(0, len(records), batch_size)
        ]
        expected = steps_per_epoch * accumulation
        if len(batches) != expected:
            raise ValueError(
                f"SkillOpt requested {expected} training batches, generated {len(batches)}"
            )
        return [
            BatchSpec(
                phase="train",
                split="train",
                seed=seed + epoch * 1000 + index,
                batch_size=len(batch),
                payload=batch,
            )
            for index, batch in enumerate(batches, 1)
        ]

    def build_train_batch(
        self, batch_size: int, seed: int, **kwargs: Any
    ) -> BatchSpec:
        records = [dict(record) for record in self.train_records]
        random.Random(seed).shuffle(records)
        batch = records[:batch_size]
        if len(batch) != batch_size:
            raise ValueError(
                f"SkillOpt requested {batch_size} training tasks, found {len(batch)}"
            )
        return BatchSpec("train", "train", seed, len(batch), batch)

    def build_eval_batch(
        self, env_num: int, split: str, seed: int, **kwargs: Any
    ) -> BatchSpec:
        if split != "valid_seen":
            raise ValueError(f"SkillOpt induction cannot access split {split!r}")
        if env_num != len(self.validation_records):
            raise ValueError(
                "SkillOpt validation must use the complete fixed validation set"
            )
        batch = [dict(record) for record in self.validation_records]
        return BatchSpec("eval", split, seed, len(batch), batch)
