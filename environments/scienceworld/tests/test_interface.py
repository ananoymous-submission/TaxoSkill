"""Public factual interface assets for the standalone ScienceWorld package."""

from scienceworld_env.interface import environment_description


def test_environment_description_is_packaged_and_carries_the_action_grammar() -> None:
    description = environment_description()

    assert "ScienceWorld is a text-based environment" in description
    assert "The available actions are:" in description
    assert "teleport to LOC" in description
    assert "focus on OBJ" in description
