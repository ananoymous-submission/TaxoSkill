"""Contract tests for the standalone ALFWorld task catalog."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib.resources import files

import pytest

from alfworld_env.catalog import catalog_sha256, get_split, get_task


def test_installable_catalog_has_one_task_authority() -> None:
    asset_directories = {
        child.name
        for child in files("alfworld_env").joinpath("assets").iterdir()
        if child.is_dir()
    }
    assert asset_directories == {"tasks", "config"}


def test_catalog_preserves_frozen_split_identity() -> None:
    expected = {
        "development": (
            "ALFWorld official train pool",
            3553,
            191,
            3743,
            "cb7f36a97ce22bd3a85faff6571be254d4c9e0fbab1a84610791f6df1c6868c3",
        ),
        "test_seen": (
            "ALFWorld valid_seen",
            140,
            3744,
            3883,
            "43f04ca957c4975f40e399f7e22aa12dff5bfc3fde782c95e64648b1d67deffb",
        ),
        "test_unseen": (
            "ALFWorld valid_unseen",
            134,
            57,
            190,
            "5ea890a7e862a2aece519940b697a5048118fbb4e298b48614b6362d0b7ba088",
        ),
    }

    for name, identity in expected.items():
        split = get_split(name)
        source, count, first_id, last_id, digest = identity
        assert split.name == name
        assert split.role == name
        assert split.source == source
        assert split.source_revision == (
            "alfworld json_2.1.1 released train/valid_seen/valid_unseen manifests"
        )
        assert len(split.tasks) == count
        assert split.tasks[0].task_id == first_id
        assert split.tasks[-1].task_id == last_id
        assert split.sha256 == digest


def test_catalog_resolves_the_complete_global_identity_range() -> None:
    tasks = tuple(
        task
        for split_name in ("test_unseen", "development", "test_seen")
        for task in get_split(split_name).tasks
    )

    assert tuple(task.task_id for task in tasks) == tuple(range(57, 3884))
    assert all(get_task(task.task_id) is task for task in tasks)
    with pytest.raises(ValueError, match="unknown ALFWorld task ID: 56"):
        get_task(56)


def test_catalog_gamefiles_are_safe_relative_paths() -> None:
    for task_id in range(57, 3884):
        gamefile = get_task(task_id).gamefile
        assert gamefile.startswith("json_2.1.1/")
        assert gamefile.endswith("/game.tw-pddl")
        assert ".." not in gamefile.split("/")
        assert not gamefile.startswith("/")


def test_catalog_has_a_deterministic_semantic_digest() -> None:
    assert catalog_sha256() == (
        "1245cf0093e669b5eb108bfd4b623ecd6e11eb7df9baf76d7c6d640a35752236"
    )


def test_catalog_records_are_immutable() -> None:
    task = get_task(57)
    with pytest.raises(FrozenInstanceError):
        task.task_id = 99  # type: ignore[misc]
