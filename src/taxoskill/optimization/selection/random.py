"""Deterministic random task selection."""

from __future__ import annotations

import hashlib
import random
from typing import Sequence

from taxoskill.optimization.selection.base import validate_selection_request
from taxoskill.optimization.tasks import OptimizationTask


def derived_seed(seed: int, namespace: str) -> int:
    if not namespace:
        raise ValueError("selection seed namespace must be non-empty")
    digest = hashlib.sha256(f"{seed}:{namespace}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


class RandomTaskSelector:
    def select(
        self,
        tasks: Sequence[OptimizationTask],
        count: int,
        *,
        seed: int,
        namespace: str,
    ) -> list[OptimizationTask]:
        validate_selection_request(tasks, count)
        rng = random.Random(derived_seed(seed, namespace))
        return rng.sample(sorted(tasks, key=lambda task: task.key), count)
