from __future__ import annotations

import pytest
from pydantic import ValidationError

from alfworld_env.models import AlfWorldAction, AlfWorldAct, native_tool_action, native_tool_specs


def test_native_tool_spec_is_generated_from_model_facing_action() -> None:
    specs = native_tool_specs()

    assert specs == (
        {
            "name": "act",
            "description": "Execute one text command in ALFWorld.",
            "input_schema": AlfWorldAct.model_json_schema(),
        },
    )
    schema = specs[0]["input_schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {"command"}
    assert "metadata" not in schema["properties"]
    assert "oneOf" not in schema
    assert "discriminator" not in schema


def test_native_tool_action_validates_arguments_and_builds_wire_action() -> None:
    action = native_tool_action("act", {"command": "look"})

    assert isinstance(action, AlfWorldAction)
    assert action.model_dump() == {"command": "look", "metadata": {}}

    with pytest.raises(ValidationError):
        native_tool_action("act", {"command": "look", "metadata": {"retry": 1}})


def test_action_accepts_native_envelope_without_changing_internal_shape() -> None:
    action = AlfWorldAction.model_validate(
        {"name": "act", "arguments": {"command": "look"}}
    )

    assert action.model_dump() == {"command": "look", "metadata": {}}

    with pytest.raises(ValidationError, match="native tool envelope"):
        AlfWorldAction.model_validate(
            {"name": "act", "arguments": {"command": "look"}, "tool": "act"}
        )


def test_native_tool_action_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError, match="unknown ALFWorld native tool"):
        native_tool_action("submit", {"command": "look"})
