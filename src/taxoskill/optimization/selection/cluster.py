"""Uniform task selection over a primitive-procedure cover."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Mapping, Sequence

from taxoskill.optimization.selection.base import validate_selection_request
from taxoskill.optimization.selection.random import derived_seed
from taxoskill.optimization.tasks import OptimizationTask, TaskKey


class ClusterTaskSelector:
    """Allocate a total task budget uniformly while covering every cluster."""

    def __init__(
        self,
        assignments: Mapping[TaskKey, tuple[int, ...]],
    ) -> None:
        if not assignments:
            raise ValueError("cluster task selector requires non-empty assignments")
        for clusters in assignments.values():
            validate_cluster_ids(clusters)
        self._assignments = dict(assignments)

    def select(
        self,
        tasks: Sequence[OptimizationTask],
        count: int,
        *,
        seed: int,
        namespace: str,
    ) -> list[OptimizationTask]:
        validate_selection_request(tasks, count)
        if count == len(tasks):
            selected = sorted(tasks, key=lambda task: task.key)
            random.Random(derived_seed(seed, namespace)).shuffle(selected)
            return selected
        clusters_of: dict[TaskKey, tuple[int, ...]] = {}
        for task in tasks:
            try:
                clusters_of[task.key] = self._assignments[task.key]
            except KeyError as error:
                raise ValueError(
                    f"task {task.key.canonical} has no partition assignment"
                ) from error
        ordered = sorted(tasks, key=lambda task: task.key)
        rng = random.Random(derived_seed(seed, namespace))
        selected = cover_select(
            ordered,
            count,
            clusters_of=lambda task: clusters_of[task.key],
            rng=rng,
        )
        if len(selected) != count:
            raise RuntimeError("cluster selector returned the wrong task count")
        return selected


def validate_cluster_ids(clusters: tuple[int, ...]) -> None:
    if not isinstance(clusters, tuple) or not clusters:
        raise ValueError("cluster assignments must be non-empty tuples of cluster ids")
    if any(not isinstance(item, int) or item < 0 for item in clusters):
        raise ValueError("cluster assignments must be non-negative integers")
    if list(clusters) != sorted(set(clusters)):
        raise ValueError("cluster assignments must be sorted and distinct")


def cover_select(
    ordered: Sequence[object],
    count: int,
    *,
    clusters_of,
    rng: random.Random,
) -> list:
    """Greedy uniform-quota cover with seeded canonical tie-breaking."""
    by_cluster: dict[int, list[object]] = defaultdict(list)
    for item in ordered:
        for cluster_id in clusters_of(item):
            by_cluster[cluster_id].append(item)
    quotas = cluster_quotas(by_cluster, count)
    remaining = dict(quotas)
    candidates = list(ordered)
    rng.shuffle(candidates)
    selected: list = []
    available = set(range(len(candidates)))
    while len(selected) < count:
        best_index, best_gain = -1, -1
        for index in sorted(available):
            gain = sum(remaining[c] > 0 for c in clusters_of(candidates[index]))
            if gain > best_gain:
                best_index, best_gain = index, gain
        chosen = candidates[best_index]
        available.discard(best_index)
        selected.append(chosen)
        for cluster_id in clusters_of(chosen):
            if remaining[cluster_id] > 0:
                remaining[cluster_id] -= 1
    uncovered = [c for c, q in quotas.items() if q > 0 and remaining[c] == q]
    if uncovered:
        raise RuntimeError(f"cover selection left clusters uncovered: {uncovered}")
    rng.shuffle(selected)
    return selected


def cluster_quotas(
    by_cluster: Mapping[int, Sequence[object]],
    count: int,
) -> dict[int, int]:
    """Allocate an exact budget uniformly across represented clusters."""
    clusters = sorted(by_cluster)
    if not clusters:
        raise ValueError("cluster quota allocation requires represented clusters")
    if count < len(clusters):
        raise ValueError(
            f"cluster selection requires at least {len(clusters)} tasks to "
            "cover every represented cluster"
        )
    target = count / len(clusters)
    quotas = {cluster_id: 1 for cluster_id in clusters}
    for _ in range(count - len(clusters)):
        eligible = [
            cluster_id
            for cluster_id in clusters
            if quotas[cluster_id] < len(by_cluster[cluster_id])
        ]
        if not eligible:
            raise RuntimeError("cluster capacities cannot satisfy selection count")
        chosen = max(
            eligible,
            key=lambda cluster_id: (target - quotas[cluster_id], -cluster_id),
        )
        quotas[chosen] += 1
    for cluster_id, quota in quotas.items():
        if quota > len(by_cluster[cluster_id]):
            raise ValueError(
                f"uniform cluster quota {quota} exceeds cluster "
                f"{cluster_id} capacity {len(by_cluster[cluster_id])}"
            )
    return quotas


def select_joint_cluster_splits(
    tasks: Sequence[OptimizationTask],
    assignments: Mapping[TaskKey, tuple[int, ...]],
    *,
    train_count: int,
    validation_count: int,
    seed: int,
) -> tuple[list[OptimizationTask], list[OptimizationTask]]:
    """Select one deterministic, disjoint cluster-uniform train/validation split.

    This is the single selection path shared by global-cluster and per-cluster training. The
    global method consumes both complete lists; a per-cluster run filters these exact lists by its
    cluster id. Selection always operates on the full canonical pool, so both architectures use
    identical task instances rather than independently re-sampling within cluster-scoped pools.
    """
    if not tasks:
        raise ValueError("joint cluster selection requires a non-empty task pool")
    keys = [task.key for task in tasks]
    if len(set(keys)) != len(keys):
        raise ValueError("joint cluster selection received duplicate task keys")

    by_cluster: dict[int, list[OptimizationTask]] = defaultdict(list)
    for task in sorted(tasks, key=lambda item: item.key):
        try:
            clusters = assignments[task.key]
        except KeyError as error:
            raise ValueError(
                f"task {task.key.canonical} has no partition assignment"
            ) from error
        validate_cluster_ids(clusters)
        if len(clusters) != 1:
            raise ValueError(
                "joint cluster selection requires exactly one cluster per task; "
                f"{task.key.canonical} has {clusters}"
            )
        by_cluster[clusters[0]].append(task)

    train_quotas, validation_quotas = joint_cluster_split_quotas(
        {cluster: len(cluster_tasks) for cluster, cluster_tasks in by_cluster.items()},
        train_count=train_count,
        validation_count=validation_count,
    )
    train: list[OptimizationTask] = []
    validation: list[OptimizationTask] = []
    for cluster in sorted(by_cluster):
        candidates = list(by_cluster[cluster])
        random.Random(derived_seed(seed, f"joint-cluster-{cluster}")).shuffle(candidates)
        n_train = train_quotas[cluster]
        n_validation = validation_quotas[cluster]
        train.extend(candidates[:n_train])
        validation.extend(candidates[n_train:n_train + n_validation])

    random.Random(derived_seed(seed, "joint-cluster-train-order")).shuffle(train)
    random.Random(derived_seed(seed, "joint-cluster-validation-order")).shuffle(validation)
    if len(train) != train_count or len(validation) != validation_count:
        raise RuntimeError("joint cluster selector returned the wrong split sizes")
    if {task.key for task in train} & {task.key for task in validation}:
        raise RuntimeError("joint cluster selector returned overlapping train/validation tasks")
    return train, validation


def joint_cluster_split_quotas(
    cluster_sizes: Mapping[int, int],
    *,
    train_count: int,
    validation_count: int,
) -> tuple[dict[int, int], dict[int, int]]:
    """Allocate disjoint train/validation budgets evenly with capacity redistribution.

    The combined budget is allocated first so a cluster's train and validation shares can never
    exceed its task capacity. The combined quota is then split proportionally, using deterministic
    largest remainders to preserve the requested global train/validation totals.
    """
    if not cluster_sizes:
        raise ValueError("joint cluster split allocation requires represented clusters")
    if train_count <= 0 or validation_count <= 0:
        raise ValueError("joint cluster split counts must be positive")
    if any(size <= 0 for size in cluster_sizes.values()):
        raise ValueError("joint cluster split capacities must be positive")

    total = train_count + validation_count
    combined = cluster_quotas(
        {cluster_id: range(size) for cluster_id, size in cluster_sizes.items()},
        total,
    )
    train = {
        cluster_id: quota * train_count // total
        for cluster_id, quota in combined.items()
    }
    remaining = train_count - sum(train.values())
    # Odd combined quotas leave a surplus task; spend it on the train side, smallest cluster
    # first (a 5-task cluster becomes 3 train / 2 validation), then by cluster id.
    ranked = sorted(
        combined,
        key=lambda cluster_id: (
            -(combined[cluster_id] * train_count % total),
            cluster_sizes[cluster_id],
            cluster_id,
        ),
    )
    for cluster_id in ranked[:remaining]:
        train[cluster_id] += 1

    validation = {
        cluster_id: combined[cluster_id] - train[cluster_id]
        for cluster_id in combined
    }
    return train, validation
