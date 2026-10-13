"""K-Means clustering selected by mean silhouette."""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from taxoskill.optimization.partitioning.methods.base import (
    CandidateResult,
    MethodResult,
    canonicalize_labels,
    method_result,
    resampling_stability_report,
    select_best,
)
from taxoskill.optimization.partitioning.methods.agglomerative import search_space

NAME = "kmeans"


def fit(
    vectors: np.ndarray, params: dict[str, int], seed: int
) -> tuple[np.ndarray, dict[str, float | int]]:
    model = KMeans(
        n_clusters=params["n_clusters"],
        init="k-means++",
        n_init=20,
        max_iter=300,
        tol=1e-4,
        algorithm="lloyd",
        random_state=seed,
    ).fit(vectors)
    return canonicalize_labels(model.labels_), {
        "inertia": float(model.inertia_),
        "n_iter": int(model.n_iter_),
    }


def run(
    vectors: np.ndarray, *, seed: int, k_max: int = 50, stability_resamples: int = 10
) -> tuple[MethodResult, list[CandidateResult]]:
    candidates: list[CandidateResult] = []
    for params in search_space(len(vectors), k_max):
        labels, diagnostics = fit(vectors, params, seed)
        diagnostics["silhouette"] = float(silhouette_score(vectors, labels, metric="euclidean"))
        candidates.append(CandidateResult(
            params=params, diagnostics=diagnostics, labels=labels.tolist()
        ))
    selected = select_best(
        candidates, metric="silhouette", tie_key=lambda candidate: candidate.params["n_clusters"]
    )
    stability = resampling_stability_report(
        vectors,
        selected.params,
        lambda data, params, run_seed: fit(data, params, run_seed)[0],
        seed=seed,
        resamples=stability_resamples,
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
