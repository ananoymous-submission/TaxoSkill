"""Unified instruction-only clustering ablation pipeline.

Examples:
    python -m taxoskill.optimization.partitioning.clustering \
        --config configs/experiments/sciworld/base.yaml --method all
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv

from taxoskill.task_files import TaskPool, load_manifest
from taxoskill.optimization.partitioning.embedding import (
    EmbeddingManifest,
    build_embedder,
    create_manifest,
    input_fingerprint,
)
from taxoskill.optimization.partitioning.methods.base import CandidateResult, MethodResult
from taxoskill.optimization.partitioning.artifact import build_method_partition
from taxoskill.optimization.partitioning.source import load_endpoint_pool

OUTPUT_ROOT = Path("outputs/partitions/clustering")
EMBEDDING_ROOT = Path("outputs/partitions/embeddings")
METHODS = ("agglomerative", "kmeans", "dbscan")
SELECTION_RULES = {
    "agglomerative": "maximize Euclidean silhouette; numerical ties prefer smaller k",
    "kmeans": "maximize Euclidean silhouette; numerical ties prefer smaller k",
    "dbscan": "maximize DBCV; ties prefer lower noise rate, then fewer clusters",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _versions() -> dict[str, str]:
    packages = ("numpy", "scipy", "scikit-learn", "hdbscan")
    versions = {"python": platform.python_version()}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def _implementation_sha256(method: str) -> str:
    """Fingerprint every source file that can change labels or saved artifact semantics."""
    partitioning = Path(__file__).resolve().parent
    repository = partitioning.parents[3]
    paths = [
        Path(__file__).resolve(),
        partitioning / "artifact.py",
        partitioning / "methods" / "base.py",
        partitioning / "methods" / f"{method}.py",
    ]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(repository)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class _PartitionContext:
    environment_asset_hashes: dict[str, str]
    environment_description: str


def _optimizer_task_indices(task_ids: list[str]) -> list[int]:
    """Preserve integer runtime IDs; map external IDs to development-file positions."""
    try:
        indices = [int(task_id) for task_id in task_ids]
    except ValueError:
        indices = list(range(len(task_ids)))
    if len(set(indices)) != len(indices):
        raise ValueError("development task IDs do not map to unique runtime indices")
    return indices


def _partition_context(
    pool: TaskPool,
    *,
    environment_root: Path | None = None,
) -> _PartitionContext:
    """Read partition metadata without importing a runtime environment or any test file."""
    if not pool.manifest_sha256:
        raise ValueError("optimizer partition export requires an explicit development task file")
    if pool.environment_asset_hashes or pool.environment_description:
        if pool.environment_asset_hashes != {
            "development_task_file": pool.manifest_sha256
        }:
            raise ValueError("endpoint development provenance differs from task pool hash")
        if not pool.environment_description.strip():
            raise ValueError("endpoint environment description is empty")
        return _PartitionContext(
            environment_asset_hashes=dict(pool.environment_asset_hashes),
            environment_description=pool.environment_description.strip(),
        )
    if environment_root is not None:
        description_path = (
            environment_root / pool.env / "assets" / "environment_description.txt"
        )
    elif pool.manifest_path is not None:
        description_path = pool.manifest_path.parent.parent / "environment_description.txt"
    else:
        raise ValueError(
            "partition context requires endpoint metadata or an explicit manifest path"
        )
    description = description_path.read_text(encoding="utf-8").strip()
    if not description:
        raise ValueError(f"empty environment description: {description_path}")
    return _PartitionContext(
        environment_asset_hashes={"development_task_file": pool.manifest_sha256},
        environment_description=description,
    )


def _search_config(method: str, k_max: int) -> dict[str, Any]:
    if method in {"agglomerative", "kmeans"}:
        return {"k_max": k_max}
    if method == "dbscan":
        from taxoskill.optimization.partitioning.methods.dbscan import (
            DEFAULT_EPS_QUANTILES,
            DEFAULT_MIN_SAMPLES,
        )
        return {
            "min_samples": list(DEFAULT_MIN_SAMPLES),
            "eps_quantiles": list(DEFAULT_EPS_QUANTILES),
        }
    raise ValueError(f"unknown clustering method {method!r}")


def _cached_result_valid(
    output: Path,
    *,
    fingerprint: str,
    array_sha256: str,
    method: str,
    seed: int,
    k_max: int,
    selection_rule: str,
) -> bool:
    labels_path = output / "labels.json"
    run_path = output / "run.json"
    sweep_path = output / "sweep.json"
    if (
        not labels_path.is_file()
        or not run_path.is_file()
        or not sweep_path.is_file()
        or (output / "failed.json").exists()
    ):
        return False
    try:
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        run = json.loads(run_path.read_text(encoding="utf-8"))
        sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (
        labels.get("schema_version") == 1
        and labels.get("embedding_fingerprint") == fingerprint
        and labels.get("embedding_array_sha256") == array_sha256
        and labels.get("method") == method
        and run.get("schema_version") == 1
        and run.get("method") == method
        and run.get("seed") == seed
        and run.get("embedding_manifest", {}).get("fingerprint") == fingerprint
        and run.get("embedding_manifest", {}).get("array_sha256") == array_sha256
        and sweep.get("schema_version") == 1
        and sweep.get("embedding_fingerprint") == fingerprint
        and sweep.get("embedding_array_sha256") == array_sha256
        and sweep.get("method") == method
        and labels.get("env") == run.get("env") == sweep.get("env")
        and run.get("search_config") == _search_config(method, k_max)
        and run.get("selection_rule") == selection_rule
        and run.get("versions") == _versions()
        and run.get("implementation_sha256") == _implementation_sha256(method)
        and labels.get("deployable") == run.get("deployable")
        and bool(run.get("partition_exported")) == (output / "partition.json").is_file()
    )


def embeddings_for(
    pool: TaskPool,
    *,
    backend: str = "remote",
    recompute: bool = False,
    cache_root: Path = EMBEDDING_ROOT,
) -> tuple[np.ndarray, EmbeddingManifest]:
    """Load or create a fingerprinted instruction-only embedding matrix."""
    embedder = build_embedder(backend)
    description = embedder.describe()
    fingerprint, _, _ = input_fingerprint(
        env=pool.env,
        task_ids=pool.task_ids,
        instructions=pool.instructions,
        embedder=description,
        task_file_sha256=pool.manifest_sha256,
    )
    directory = cache_root / pool.env
    array_path = directory / f"{fingerprint}.npy"
    manifest_path = directory / f"{fingerprint}.json"
    if array_path.is_file() and manifest_path.is_file() and not recompute:
        vectors = np.load(array_path)
        manifest = create_manifest(
            env=pool.env,
            task_ids=pool.task_ids,
            instructions=pool.instructions,
            vectors=vectors,
            embedder=description,
            task_file_sha256=pool.manifest_sha256,
        )
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        if saved != manifest.to_dict():
            raise ValueError(f"embedding cache failed provenance validation: {manifest_path}")
        return vectors, manifest

    vectors = embedder.encode(pool.instructions, show_progress=True)
    manifest = create_manifest(
        env=pool.env,
        task_ids=pool.task_ids,
        instructions=pool.instructions,
        vectors=vectors,
        embedder=description,
        task_file_sha256=pool.manifest_sha256,
    )
    directory.mkdir(parents=True, exist_ok=True)
    np.save(array_path, vectors)
    _write_json(manifest_path, manifest.to_dict())
    return vectors, manifest


def _run_method(
    method: str, vectors: np.ndarray, *, seed: int, k_max: int
) -> tuple[MethodResult, list[CandidateResult]]:
    if method == "agglomerative":
        from taxoskill.optimization.partitioning.methods.agglomerative import run
        return run(vectors, seed=seed, k_max=k_max)
    if method == "kmeans":
        from taxoskill.optimization.partitioning.methods.kmeans import run
        return run(vectors, seed=seed, k_max=k_max)
    if method == "dbscan":
        from taxoskill.optimization.partitioning.methods.dbscan import run
        return run(vectors, seed=seed)
    raise ValueError(f"unknown method {method!r}; expected one of {METHODS}")


def run_from_vectors(
    pool: TaskPool,
    vectors: np.ndarray,
    manifest: EmbeddingManifest,
    *,
    method: str,
    seed: int,
    output_root: Path = OUTPUT_ROOT,
    k_max: int = 50,
    export_partition: bool = True,
) -> Path:
    """Run one method, freeze label-free artifacts, then append external evaluation."""
    if tuple(pool.task_ids) != manifest.task_ids or len(vectors) != len(pool):
        raise ValueError("task pool and embedding manifest do not align")
    observed_manifest = create_manifest(
        env=pool.env,
        task_ids=pool.task_ids,
        instructions=pool.instructions,
        vectors=vectors,
        embedder=manifest.embedder,
        task_file_sha256=pool.manifest_sha256,
    )
    if observed_manifest.to_dict() != manifest.to_dict():
        raise ValueError("embedding manifest does not match the supplied vector array")
    output = output_root / pool.env / method
    output.mkdir(parents=True, exist_ok=True)
    # Fail closed: a forced rerun must never leave an older optimizer partition loadable.
    (output / "partition.json").unlink(missing_ok=True)
    result, candidates = _run_method(method, vectors, seed=seed, k_max=k_max)
    partition_exported = bool(export_partition and result.deployable)
    if not partition_exported:
        (output / "partition.json").unlink(missing_ok=True)

    selected_index = next(
        index
        for index, candidate in enumerate(candidates)
        if candidate.params == result.selected_params and candidate.labels == result.labels
    )
    search_diagnostics: dict[str, Any] = {}
    if method == "dbscan":
        from taxoskill.optimization.partitioning.methods.dbscan import k_distance_curves

        search_diagnostics["k_distance_curves"] = {
            str(key): values for key, values in k_distance_curves(vectors).items()
        }
    _write_json(output / "sweep.json", {
        "schema_version": 1,
        "env": pool.env,
        "method": method,
        "embedding_fingerprint": manifest.fingerprint,
        "embedding_array_sha256": manifest.array_sha256,
        "selection_metric": "silhouette" if method in {"agglomerative", "kmeans"}
        else "dbcv" if method == "dbscan" else "relative_validity",
        "selection_rule": SELECTION_RULES[method],
        "selected_index": selected_index,
        "search_diagnostics": search_diagnostics,
        "candidates": [candidate.to_dict() for candidate in candidates],
    })
    _write_json(output / "run.json", {
        "schema_version": 1,
        "env": pool.env,
        "method": method,
        "seed": seed,
        "embedding_manifest": manifest.to_dict(),
        "selected_params": result.selected_params,
        "search_config": _search_config(method, k_max),
        "selection_rule": SELECTION_RULES[method],
        "versions": _versions(),
        "implementation_sha256": _implementation_sha256(method),
        "deployable": result.deployable,
        "partition_exported": partition_exported,
        "deployability_reason": None if result.deployable else "density clustering left noise tasks",
    })

    _write_json(output / "labels.json", {
        "schema_version": 1,
        "env": pool.env,
        "method": method,
        "embedding_fingerprint": manifest.fingerprint,
        "embedding_array_sha256": manifest.array_sha256,
        "task_ids": pool.task_ids,
        "labels": dict(zip(pool.task_ids, result.labels, strict=True)),
        "selected_params": result.selected_params,
        "intrinsic_diagnostics": result.diagnostics,
        "n_clusters": result.n_clusters,
        "n_noise": result.n_noise,
        "noise_rate": result.noise_rate,
        "cluster_sizes": result.cluster_sizes,
        "deployable": result.deployable,
    })
    if partition_exported:
        context = _partition_context(pool)
        artifact = build_method_partition(
            pool=pool,
            optimizer_task_indices=_optimizer_task_indices(pool.task_ids),
            result=result,
            environment_asset_hashes=context.environment_asset_hashes,
            environment_description=context.environment_description,
            train_source_split="development",
            validation_source_split="development",
            shared_development_pool=True,
            embedding_fingerprint=manifest.fingerprint,
            embedding_array_sha256=manifest.array_sha256,
            embedding_model=str(manifest.embedder["model"]),
        )
        (output / "partition.json").write_text(
            artifact.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
    return output


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", type=Path)
    source.add_argument("--manifest", type=Path)
    parser.add_argument("--method", choices=(*METHODS, "all"), default="all")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--k-max", type=int, default=50)
    parser.add_argument("--backend", choices=("remote", "local"), default="remote")
    parser.add_argument("--recompute-embeddings", action="store_true")
    parser.add_argument("--force-sweep", action="store_true")
    parser.add_argument(
        "--no-partition",
        action="store_true",
        help="run clustering analysis without exporting an optimizer partition",
    )
    args = parser.parse_args()

    pool = (
        load_endpoint_pool(args.config)
        if args.config is not None
        else load_manifest(args.manifest, require_role="development")
    )
    vectors, manifest = embeddings_for(
        pool, backend=args.backend, recompute=args.recompute_embeddings
    )
    methods = METHODS if args.method == "all" else (args.method,)
    failures: list[str] = []
    for method in methods:
        output = OUTPUT_ROOT / pool.env / method
        if not args.force_sweep and _cached_result_valid(
            output,
            fingerprint=manifest.fingerprint,
            array_sha256=manifest.array_sha256,
            method=method,
            seed=args.seed,
            k_max=args.k_max,
            selection_rule=SELECTION_RULES[method],
        ):
            print(f"[clustering] {method}: valid cached result at {output}", flush=True)
            continue
        try:
            output = run_from_vectors(
                pool,
                vectors,
                manifest,
                method=method,
                seed=args.seed,
                k_max=args.k_max,
                export_partition=not args.no_partition,
            )
            (output / "failed.json").unlink(missing_ok=True)
            print(f"[clustering] {method}: wrote {output}", flush=True)
        except Exception as error:
            failures.append(f"{method}: {error}")
            failed = OUTPUT_ROOT / pool.env / method / "failed.json"
            (failed.parent / "partition.json").unlink(missing_ok=True)
            _write_json(failed, {"method": method, "error": str(error)})
            print(f"[clustering] {method}: FAILED: {error}", flush=True)
    if failures:
        raise SystemExit("clustering failures:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
