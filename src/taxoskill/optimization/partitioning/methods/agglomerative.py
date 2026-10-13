"""Ward agglomerative clustering selected by mean silhouette."""

from __future__ import annotations

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from taxoskill.optimization.partitioning.methods.base import (
    CandidateResult,
    MethodResult,
    canonicalize_labels,
    method_result,
    resampling_stability_report,
    select_best,
)

NAME = "agglomerative"


def search_space(n_samples: int, k_max: int = 50) -> list[dict[str, int]]:
    upper = min(k_max, n_samples - 1)
    if upper < 2:
        raise ValueError("agglomerative clustering requires at least three samples")
    return [{"n_clusters": k} for k in range(2, upper + 1)]


def fit(vectors: np.ndarray, params: dict[str, int], seed: int = 0) -> np.ndarray:
    del seed
    labels = AgglomerativeClustering(
        n_clusters=params["n_clusters"], linkage="ward", metric="euclidean"
    ).fit_predict(vectors)
    return canonicalize_labels(labels)


def run(
    vectors: np.ndarray, *, seed: int, k_max: int = 50, stability_resamples: int = 10
) -> tuple[MethodResult, list[CandidateResult]]:
    candidates: list[CandidateResult] = []
    for params in search_space(len(vectors), k_max):
        labels = fit(vectors, params, seed)
        candidates.append(CandidateResult(
            params=params,
            diagnostics={"silhouette": float(silhouette_score(vectors, labels, metric="euclidean"))},
            labels=labels.tolist(),
        ))
    selected = select_best(
        candidates, metric="silhouette", tie_key=lambda candidate: candidate.params["n_clusters"]
    )
    stability = resampling_stability_report(
        vectors, selected.params, fit, seed=seed, resamples=stability_resamples
    )
    selected = CandidateResult(
        params=selected.params,
        diagnostics={
            **selected.diagnostics,
            "search_boundary_selected": selected.params["n_clusters"] == min(k_max, len(vectors) - 1),
            "resampling_stability": stability["mean"],
            "resampling_stability_std": stability["std"],
            "resampling_stability_pairs": stability["n_comparisons"],
        },
        labels=selected.labels,
    )
    return method_result(NAME, selected, seed), candidates
