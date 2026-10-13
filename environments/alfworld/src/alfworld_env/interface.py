"""Factual ALFWorld environment interface description."""

from __future__ import annotations

from importlib.resources import files


def environment_description() -> str:
    """Return the label-free ALFWorld affordance description."""
    text = (
        files("alfworld_env")
        .joinpath("assets", "environment_description.txt")
        .read_text(encoding="utf-8")
        .strip()
    )
    if not text:
        raise ValueError("empty ALFWorld environment description")
    return text
