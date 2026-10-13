"""Contract tests for the standalone ScienceWorld task catalog."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib.resources import files

import pytest

from scienceworld_env.catalog import (
    catalog_sha256,
    get_split,
    get_task,
)


def test_installable_catalog_has_one_task_authority() -> None:
    asset_directories = {
        child.name
        for child in files("scienceworld_env").joinpath("assets").iterdir()
        if child.is_dir()
    }

    assert asset_directories == {"tasks"}


def test_catalog_preserves_frozen_split_identity() -> None:
    expected = {
        "development": (
            "ETO train",
            "development",
            1483,
            0,
            1482,
            "bd986b372b1835739eeee78b59782a56e08d5ff2492a8bd5fed90349c5d151ce",
        ),
        "test_seen": (
            "ETO dev",
            "test_seen",
            194,
            1483,
            1676,
            "aff4333a95331dcc5add748169e69660a9aef7b0b786d120f9e6d15b219e0166",
        ),
        "test_unseen": (
            "ETO test",
            "test_unseen",
            211,
            1677,
            1887,
            "455a80fe5361c48fc7404263438b5e75bdefddecd23235a2c9cf0464e2a22a18",
        ),
    }

    for name, identity in expected.items():
        split = get_split(name)
        source, role, count, first_id, last_id, digest = identity
        assert split.name == name
        assert split.source == source
        assert split.role == role
        assert split.source_revision == (
            "allenai/eto a2fc5da38f8d00cfaf3f9b6370d586eebaf72904"
        )
        assert len(split.tasks) == count
        assert split.tasks[0].task_id == first_id
        assert split.tasks[-1].task_id == last_id
        assert split.sha256 == digest


def test_catalog_resolves_each_stable_global_task_id() -> None:
    tasks = tuple(
        task
        for split_name in ("development", "test_seen", "test_unseen")
        for task in get_split(split_name).tasks
    )

    assert tuple(task.task_id for task in tasks) == tuple(range(1888))
    assert all(get_task(task.task_id) is task for task in tasks)
    with pytest.raises(ValueError, match="unknown ScienceWorld task ID: 1888"):
        get_task(1888)


def test_catalog_includes_task_text_for_every_split() -> None:
    for split_name in ("development", "test_seen", "test_unseen"):
        for task in get_split(split_name).tasks:
            assert task.instruction.strip()
            assert task.initial_observation.strip()


def test_catalog_has_a_deterministic_semantic_digest() -> None:
    assert catalog_sha256() == (
        "db23a7ede8b16a407dc0ee977e592389c7038d918bb9149ee42461a79d24b52d"
    )


def test_catalog_records_are_immutable() -> None:
    task = get_task(0)

    with pytest.raises(FrozenInstanceError):
        task.task_id = 99  # type: ignore[misc]
