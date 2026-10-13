"""Private text-only ALFWorld backend used by the canonical core."""

from __future__ import annotations

from importlib.resources import files
import os
from pathlib import Path
from typing import Any

import yaml

from alfworld_env.core import BackendObservation


def _create_single_alfred_env(config: dict[str, Any]):
    from alfworld.agents.environment.alfred_tw_env import (  # type: ignore[import-not-found]
        AlfredTWEnv,
    )

    class SingleAlfredTWEnv(AlfredTWEnv):
        """Benchmark-specific upstream env owning exactly one gamefile."""

        def __init__(self, config: dict[str, Any]) -> None:
            self.config = config
            self.train_eval = "eval_out_of_distribution"
            self.goal_desc_human_anns_prob = config["env"][
                "goal_desc_human_anns_prob"
            ]
            self.get_game_logic()
            self.random_seed = 42
            self.game_files: list[str] = []
            self.num_games = 0

    return SingleAlfredTWEnv(config)


class TextAlfWorldBackend:
    """Own one upstream ALFWorld TextWorld engine at a time."""

    def __init__(self, data_path: str | Path | None = None) -> None:
        root = Path(
            data_path
            if data_path is not None
            else os.getenv("ALFWORLD_DATA", "~/.cache/alfworld")
        ).expanduser()
        self._data_path = root.resolve()
        dataset_root = self._data_path / "json_2.1.1"
        if not dataset_root.is_dir():
            raise FileNotFoundError(
                f"ALFWorld data is missing json_2.1.1 under {self._data_path}"
            )
        os.environ["ALFWORLD_DATA"] = str(self._data_path)
        config_text = (
            files("alfworld_env")
            .joinpath("assets", "config", "base_config.yaml")
            .read_text(encoding="utf-8")
        )
        config = yaml.safe_load(config_text)
        if not isinstance(config, dict):
            raise TypeError("ALFWorld text configuration must be a mapping")
        config["general"]["use_cuda"] = False
        self._alfred_env = _create_single_alfred_env(config)
        self._engine = None
        self._runtime_task_type = ""
        self._closed = False

    def reset(self, gamefile: str) -> BackendObservation:
        self._ensure_open()
        resolved = self._resolve_gamefile(gamefile)
        if self._engine is not None:
            self._engine.close()
            self._engine = None
        self._alfred_env.game_files = [str(resolved)]
        self._alfred_env.num_games = 1
        self._engine = self._alfred_env.init_env(batch_size=1)
        observations, info = self._engine.reset()
        self._runtime_task_type = "/".join(
            str(info["extra.gamefile"][0]).split("/")[-3:-1]
        )
        return BackendObservation(
            text=str(observations[0]),
            admissible_actions=self._available_actions(info),
            runtime_task_type=self._runtime_task_type,
            reward=0.0,
            terminated=False,
        )

    def step(self, action: str) -> BackendObservation:
        self._ensure_open()
        if self._engine is None or not self._runtime_task_type:
            raise RuntimeError("ALFWorld backend must be reset before step")
        observations, _, dones, info = self._engine.step([action])
        return BackendObservation(
            text=str(observations[0]),
            admissible_actions=self._available_actions(info),
            runtime_task_type=self._runtime_task_type,
            reward=float(info["won"][0]),
            terminated=bool(dones[0]),
        )

    def close(self) -> None:
        if self._closed:
            return
        if self._engine is not None:
            self._engine.close()
            self._engine = None
        self._closed = True

    def _resolve_gamefile(self, gamefile: str) -> Path:
        root = (self._data_path / "json_2.1.1").resolve()
        resolved = (self._data_path / gamefile).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("gamefile must resolve inside ALFWorld json_2.1.1")
        if not resolved.is_file():
            raise FileNotFoundError(f"ALFWorld gamefile does not exist: {gamefile}")
        return resolved

    @staticmethod
    def _available_actions(info: dict[str, Any]) -> tuple[str, ...]:
        commands = info["admissible_commands"]
        if not isinstance(commands, list) or len(commands) != 1:
            raise ValueError(
                "ALFWorld must return one admissible-command list per environment"
            )
        actions = commands[0]
        if not isinstance(actions, list) or not actions:
            raise ValueError("ALFWorld returned no admissible actions")
        if any(not isinstance(action, str) or not action.strip() for action in actions):
            raise ValueError("ALFWorld returned an invalid admissible action")
        return tuple(actions)

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("ALFWorld backend is closed")
