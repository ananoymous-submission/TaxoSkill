from __future__ import annotations

import pytest
from pydantic import ValidationError

from scienceworld_env import models


def test_native_tool_spec_is_generated_from_model_facing_action_fields() -> None:
    assert hasattr(models, "ScienceWorldAct")
    assert hasattr(models, "native_tool_specs")
    assert models.native_tool_specs() == (
        {
            "name": "act",
            "description": "Execute one text command in ScienceWorld.",
            "input_schema": models.ScienceWorldAct.model_json_schema(),
        },
    )
    schema = models.native_tool_specs()[0]["input_schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"command"}
    assert "metadata" not in schema["properties"]
    assert "oneOf" not in schema
    assert "discriminator" not in schema


def test_native_tool_call_constructs_the_existing_openenv_action() -> None:
    action = models.native_tool_action("act", {"command": "look around"})

    assert isinstance(action, models.ScienceWorldAction)
    assert action.command == "look around"
    assert action.metadata == {}

    with pytest.raises(ValidationError):
        models.native_tool_action(
            "act", {"command": "look around", "metadata": {"retry": 1}}
        )


def test_action_accepts_the_uniform_native_call_envelope() -> None:
    action = models.ScienceWorldAction.model_validate(
        {"name": "act", "arguments": {"command": "inventory"}}
    )

    assert action.command == "inventory"
    assert action.metadata == {}

    with pytest.raises(ValidationError):
        models.ScienceWorldAction.model_validate(
            {
                "name": "act",
                "arguments": {"command": "inventory"},
                "tool": "act",
            }
        )


def test_action_keeps_accepting_its_direct_payload() -> None:
    assert models.ScienceWorldAction.model_validate(
        {"command": "look around"}
    ).command == "look around"


def test_native_tool_action_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError, match="unknown ScienceWorld native tool"):
        models.native_tool_action("submit", {"command": "look around"})
