"""DBSCAN with reproducible k-distance epsilon candidates and DBCV selection."""

from __future__ import annotations

from collections.abc import Sequence
import warnings

import numpy as np
from hdbscan.validity import validity_index
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import NearestNeighbors

from taxoskill.optimization.partitioning.methods.base import (
    CandidateResult,
    MethodResult,
    canonicalize_labels,
    method_result,
    resampling_stability_report,
    select_best,
    summarize_labels,
)

NAME = "dbscan"
DEFAULT_MIN_SAMPLES = (5, 10, 20)
DEFAULT_EPS_QUANTILES = tuple(np.linspace(0.50, 0.99, 20).tolist())


def k_distance_curves(
    vectors: np.ndarray,
    *,
    min_samples_values: Sequence[int] = DEFAULT_MIN_SAMPLES,
    distance_matrix: np.ndarray | None = None,
) -> dict[int, list[float]]:
    """Sorted k-nearest-neighbor distances used to derive reproducible eps candidates."""
    curves: dict[int, list[float]] = {}
    for min_samples in min_samples_values:
        if min_samples < 2 or min_samples > len(vectors):
            continue
        if distance_matrix is None:
            distances, _ = NearestNeighbors(
                n_neighbors=min_samples, metric="euclidean"
            ).fit(vectors).kneighbors(vectors)
            kth = distances[:, -1]
        else:
            if distance_matrix.shape != (len(vectors), len(vectors)):
                raise ValueError("distance matrix does not match embedding rows")
            kth = np.partition(distance_matrix, min_samples - 1, axis=1)[:, min_samples - 1]
        curves[int(min_samples)] = sorted(float(value) for value in kth)
    return curves


def build_search_space(
    vectors: np.ndarray,
    *,
    distance_matrix: np.ndarray | None = None,
    min_samples_values: Sequence[int] = DEFAULT_MIN_SAMPLES,
    eps_quantiles: Sequence[float] = DEFAULT_EPS_QUANTILES,
) -> list[dict[str, float | int]]:
    if vectors.ndim != 2 or len(vectors) < 3:
        raise ValueError("vectors must contain at least three samples")
    params: list[dict[str, float | int]] = []
    seen: set[tuple[int, float]] = set()
    curves = k_distance_curves(
        vectors,
        min_samples_values=min_samples_values,
        distance_matrix=distance_matrix,
    )
    for min_samples, kth in curves.items():
        for quantile in eps_quantiles:
            if not 0 < quantile < 1:
                raise ValueError("epsilon quantiles must lie strictly between zero and one")
            eps = float(np.quantile(kth, quantile))
            key = (int(min_samples), eps)
            if eps > 0 and key not in seen:
                seen.add(key)
                params.append({
                    "eps": eps,
                    "min_samples": int(min_samples),
                    "eps_quantile": float(quantile),
                })
    if not params:
        raise ValueError("DBSCAN search space is empty")
    return params


def fit(vectors: np.ndarray, params: dict[str, float | int], seed: int = 0) -> np.ndarray:
    del seed
    labels = DBSCAN(
        eps=float(params["eps"]),
        min_samples=int(params["min_samples"]),
        metric="euclidean",
    ).fit_predict(vectors)
    return canonicalize_labels(labels)


def _candidate(
    vectors: np.ndarray, distance_matrix: np.ndarray, params: dict[str, float | int]
) -> CandidateResult:
    labels = canonicalize_labels(DBSCAN(
        eps=float(params["eps"]),
        min_samples=int(params["min_samples"]),
        metric="precomputed",
    ).fit_predict(distance_matrix))
    summary = summarize_labels(labels)
    diagnostics = {
        "n_clusters": summary["n_clusters"],
        "n_noise": summary["n_noise"],
        "noise_rate": summary["noise_rate"],
        "eps_quantile": params["eps_quantile"],
    }
    if summary["n_clusters"] < 2:
        return CandidateResult(
            params=params, diagnostics=diagnostics, labels=labels.tolist(),
            valid=False, rejection_reason="fewer than two non-noise clusters",
        )
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            score = float(validity_index(
                distance_matrix, labels, metric="precomputed", d=vectors.shape[1]
            ))
    except (ValueError, FloatingPointError, ZeroDivisionError) as error:
        return CandidateResult(
            params=params, diagnostics=diagnostics, labels=labels.tolist(),
            valid=False, rejection_reason=f"DBCV undefined: {error}",
        )
    if not np.isfinite(score):
        return CandidateResult(
            params=params, diagnostics=diagnostics, labels=labels.tolist(),
            valid=False, rejection_reason="DBCV is not finite",
        )
    diagnostics["dbcv"] = score
    diagnostics["dbcv_warning_count"] = len(caught)
    return CandidateResult(params=params, diagnostics=diagnostics, labels=labels.tolist())


def run(
    vectors: np.ndarray,
    *,
    seed: int,
    min_samples_values: Sequence[int] = DEFAULT_MIN_SAMPLES,
    eps_quantiles: Sequence[float] = DEFAULT_EPS_QUANTILES,
    stability_resamples: int = 10,
    distance_matrix: np.ndarray | None = None,
) -> tuple[MethodResult, list[CandidateResult]]:
    if distance_matrix is None:
        distance_matrix = pairwise_distances(vectors, metric="euclidean").astype(np.float64)
    else:
        distance_matrix = np.asarray(distance_matrix, dtype=np.float64)
    candidates = [
        _candidate(vectors, distance_matrix, params)
        for params in build_search_space(
            vectors,
            distance_matrix=distance_matrix,
            min_samples_values=min_samples_values,
            eps_quantiles=eps_quantiles,
        )
    ]
    selected = select_best(
        candidates,
        metric="dbcv",
        tie_key=lambda candidate: (
            candidate.diagnostics["noise_rate"],
            candidate.diagnostics["n_clusters"],
        ),
    )
    stability = resampling_stability_report(
        vectors, selected.params, fit, seed=seed, resamples=stability_resamples
    )
    selected = CandidateResult(
        params=selected.params,
        diagnostics={
            **selected.diagnostics,
            "resampling_stability": stability["mean"],
            "resampling_stability_std": stability["std"],
            "resampling_stability_pairs": stability["n_comparisons"],
        },
        labels=selected.labels,
    )
    return method_result(NAME, selected, seed), candidates
