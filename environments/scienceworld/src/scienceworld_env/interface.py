"""Factual ScienceWorld environment description."""

from __future__ import annotations

from importlib.resources import files


def _read_asset(name: str) -> str:
    text = files("scienceworld_env").joinpath("assets", name).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"empty ScienceWorld interface asset: {name}")
    return text


def environment_description() -> str:
    """Return the label-free environment affordance description."""
    return _read_asset("environment_description.txt")
