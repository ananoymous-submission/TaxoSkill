"""Package-boundary tests for the standalone ScienceWorld environment."""

from __future__ import annotations

import subprocess
import sys


def test_package_import_does_not_load_runtime_frameworks() -> None:
    probe = """
import sys
import scienceworld_env
import scienceworld_env.catalog
import scienceworld_env.core

for forbidden in ("taxoskill", "openenv", "scienceworld"):
    loaded = [
        name
        for name in sys.modules
        if name == forbidden or name.startswith(f"{forbidden}.")
    ]
    assert not loaded, f"importing the ScienceWorld catalog loaded {forbidden}: {loaded}"
"""
    subprocess.run([sys.executable, "-c", probe], check=True)
