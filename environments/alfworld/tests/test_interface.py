"""Public interface assets for the standalone ALFWorld package."""

from alfworld_env.interface import environment_description


def test_environment_description_is_the_skillopt_actor_line() -> None:
    # The SkillOpt ALFWorld harness gives the actor exactly this sentence plus the admissible
    # actions; the description carries nothing more so the actor is not told the world rules.
    assert environment_description() == (
        "You are an expert agent operating in the ALFRED Embodied Environment."
    )
