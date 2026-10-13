"""Optional MLflow tracking setup."""

from __future__ import annotations

from typing import Any

import mlflow

from taxoskill.config import TrackingCfg


def setup_tracking(cfg: TrackingCfg) -> None:
    mlflow.set_tracking_uri(cfg.tracking_uri)
    mlflow.set_experiment(cfg.experiment)


def flatten_params(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested config dict to dotted keys for `mlflow.log_params` (scalar leaves only)."""
    flat: dict[str, Any] = {}
    for key, value in d.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_params(value, dotted))
        else:
            flat[dotted] = value
    return flat
