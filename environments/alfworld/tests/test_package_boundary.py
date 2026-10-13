"""Package-boundary tests for the standalone ALFWorld environment."""

from __future__ import annotations

import subprocess
import sys


def test_package_import_does_not_load_runtime_frameworks() -> None:
    probe = """
import sys
import alfworld_env
import alfworld_env.catalog
import alfworld_env.core

for forbidden in ("taxoskill", "openenv", "alfworld", "textworld"):
    loaded = [
        name
        for name in sys.modules
        if name == forbidden or name.startswith(f"{forbidden}.")
    ]
    assert not loaded, f"importing alfworld_env loaded {forbidden}: {loaded}"
"""
    subprocess.run([sys.executable, "-c", probe], check=True)
