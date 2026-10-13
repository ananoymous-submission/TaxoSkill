"""Real-runtime construction contracts without importing heavy dependencies."""

from __future__ import annotations

import sys
from types import ModuleType

from alfworld_env.catalog import get_task
from alfworld_env.runtime import TextAlfWorldBackend


class FakeEngine:
    instances: list["FakeEngine"] = []

    def __init__(self, gamefiles: list[str], batch_size: int) -> None:
        self.gamefiles = gamefiles
        self.batch_size = batch_size
        self.closed = False
        self.step_calls: list[list[str]] = []
        FakeEngine.instances.append(self)

    def reset(self):
        return ["Room. Your task is to: inspect the alarmclock."], {
            "extra.gamefile": [self.gamefiles[0]],
            "admissible_commands": [["look"]],
        }

    def step(self, actions: list[str]):
        self.step_calls.append(actions)
        return (
            ["You look around."],
            [0.0],
            [False],
            {
                "admissible_commands": [["look"]],
                "won": [False],
            },
        )

    def close(self) -> None:
        self.closed = True


class FakeAlfredTWEnv:
    def get_game_logic(self) -> None:
        self.game_logic_loaded = True

    def init_env(self, batch_size: int) -> FakeEngine:
        return FakeEngine(list(self.game_files), batch_size)


def _install_fake_runtime_modules(monkeypatch) -> None:
    alfworld = ModuleType("alfworld")
    agents = ModuleType("alfworld.agents")
    environment = ModuleType("alfworld.agents.environment")
    alfred = ModuleType("alfworld.agents.environment.alfred_tw_env")
    setattr(alfred, "AlfredTWEnv", FakeAlfredTWEnv)

    modules = {
        "alfworld": alfworld,
        "alfworld.agents": agents,
        "alfworld.agents.environment": environment,
        "alfworld.agents.environment.alfred_tw_env": alfred,
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)


def _write_gamefile(tmp_path, task) -> str:
    gamefile = tmp_path / task.gamefile
    gamefile.parent.mkdir(parents=True)
    gamefile.write_text("{}", encoding="utf-8")
    return str(gamefile)


def test_reset_owns_exactly_one_gamefile_via_the_upstream_init_env_path(
    monkeypatch,
    tmp_path,
) -> None:
    _install_fake_runtime_modules(monkeypatch)
    FakeEngine.instances.clear()
    task = get_task(191)
    resolved = _write_gamefile(tmp_path, task)

    backend = TextAlfWorldBackend(data_path=tmp_path)

    assert backend._alfred_env.train_eval == "eval_out_of_distribution"
    assert backend._alfred_env.game_logic_loaded is True
    assert FakeEngine.instances == []

    observation = backend.reset(task.gamefile)

    assert len(FakeEngine.instances) == 1
    engine = FakeEngine.instances[0]
    assert engine.gamefiles == [resolved]
    assert engine.batch_size == 1
    assert backend._alfred_env.game_files == [resolved]
    assert backend._alfred_env.num_games == 1
    assert observation.admissible_actions == ("look",)
    assert observation.runtime_task_type == "/".join(resolved.split("/")[-3:-1])
    assert observation.reward == 0.0
    assert observation.terminated is False


def test_reset_closes_the_prior_engine_before_initializing_the_next(
    monkeypatch,
    tmp_path,
) -> None:
    _install_fake_runtime_modules(monkeypatch)
    FakeEngine.instances.clear()
    task = get_task(191)
    _write_gamefile(tmp_path, task)

    backend = TextAlfWorldBackend(data_path=tmp_path)
    backend.reset(task.gamefile)
    backend.reset(task.gamefile)

    assert len(FakeEngine.instances) == 2
    first, second = FakeEngine.instances
    assert first.closed is True
    assert second.closed is False

    backend.close()
    assert second.closed is True
    backend.close()
