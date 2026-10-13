"""Shared contracts for label-free clustering methods."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any, Callable, Sequence

import numpy as np
from sklearn.metrics import adjusted_rand_score


@dataclass(frozen=True)
class CandidateResult:
    params: dict[str, Any]
    diagnostics: dict[str, Any]
    labels: list[int]
    valid: bool = True
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MethodResult:
    method: str
    selected_params: dict[str, Any]
    diagnostics: dict[str, Any]
    labels: list[int]
    n_clusters: int
    n_noise: int
    noise_rate: float
    cluster_sizes: dict[int, int]
    deployable: bool
    seed: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonicalize_labels(labels: Sequence[int]) -> np.ndarray:
    """Rename non-noise clusters by first occurrence; preserve noise as ``-1``."""
    array = np.asarray(labels, dtype=int)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("labels must be a non-empty one-dimensional sequence")
    mapping: dict[int, int] = {}
    result = np.empty_like(array)
    for index, label in enumerate(array.tolist()):
        if label == -1:
            result[index] = -1
            continue
        if label < -1:
            raise ValueError(f"invalid negative cluster label {label}")
        mapping.setdefault(label, len(mapping))
        result[index] = mapping[label]
    return result


def summarize_labels(labels: Sequence[int]) -> dict[str, Any]:
    array = canonicalize_labels(labels)
    non_noise = array[array != -1]
    unique, counts = np.unique(non_noise, return_counts=True)
    sizes = {int(label): int(count) for label, count in zip(unique, counts)}
    n_noise = int(np.sum(array == -1))
    return {
        "n_clusters": len(sizes),
        "n_noise": n_noise,
        "noise_rate": n_noise / len(array),
        "cluster_sizes": sizes,
        "deployable": n_noise == 0,
    }


def resampling_stability_report(
    vectors: np.ndarray,
    params: dict[str, Any],
    fit: Callable[[np.ndarray, dict[str, Any], int], Sequence[int]],
    *,
    seed: int,
    resamples: int = 10,
    fraction: float = 0.8,
) -> dict[str, float | int]:
    """ARI mean/dispersion on overlaps of fixed-seed subsample refits."""
    if resamples < 2:
        raise ValueError("stability requires at least two resamples")
    if not 0 < fraction <= 1:
        raise ValueError("stability fraction must lie in (0, 1]")
    sample_size = max(2, int(round(len(vectors) * fraction)))
    rng = np.random.default_rng(seed)
    fitted: list[tuple[np.ndarray, np.ndarray]] = []
    for index in range(resamples):
        selected = np.sort(rng.choice(len(vectors), size=sample_size, replace=False))
        labels = np.asarray(fit(vectors[selected], params, seed + index), dtype=int)
        if labels.shape != (sample_size,):
            raise ValueError("stability refit returned misaligned labels")
        fitted.append((selected, labels))
    scores: list[float] = []
    for left in range(len(fitted)):
        left_ids, left_labels = fitted[left]
        for right in range(left + 1, len(fitted)):
            right_ids, right_labels = fitted[right]
            _, left_positions, right_positions = np.intersect1d(
                left_ids, right_ids, return_indices=True
            )
            if len(left_positions) >= 2:
                scores.append(float(adjusted_rand_score(
                    left_labels[left_positions], right_labels[right_positions]
                )))
    if not scores:
        raise ValueError("stability resamples have no usable overlap")
    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "n_comparisons": len(scores),
    }


def select_best(
    candidates: Sequence[CandidateResult],
    *,
    metric: str,
    tie_key: Callable[[CandidateResult], Any],
    tolerance: float = 1e-12,
) -> CandidateResult:
    valid = [candidate for candidate in candidates if candidate.valid]
    if not valid:
        raise ValueError("no valid clustering candidates")
    for candidate in valid:
        score = candidate.diagnostics.get(metric)
        if not isinstance(score, (int, float)) or not isfinite(float(score)):
            raise ValueError(f"candidate metric {metric!r} must be finite")
    best_score = max(float(candidate.diagnostics[metric]) for candidate in valid)
    tied = [
        candidate
        for candidate in valid
        if best_score - float(candidate.diagnostics[metric]) <= tolerance
    ]
    return min(tied, key=tie_key)


def method_result(method: str, candidate: CandidateResult, seed: int) -> MethodResult:
    labels = canonicalize_labels(candidate.labels).tolist()
    summary = summarize_labels(labels)
    if summary["n_clusters"] < 2:
        raise ValueError("a final clustering must contain at least two non-noise clusters")
    return MethodResult(
        method=method,
        selected_params=candidate.params,
        diagnostics=candidate.diagnostics,
        labels=labels,
        seed=seed,
        **summary,
    )
