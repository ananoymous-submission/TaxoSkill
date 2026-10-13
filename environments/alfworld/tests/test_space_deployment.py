"""Deployment contract for the bucket-backed ALFWorld Docker Space."""

from __future__ import annotations

from pathlib import Path

import tomllib


PACKAGE_ROOT = Path(__file__).parents[1]


def test_server_extra_installs_pinned_text_runtime() -> None:
    pyproject = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = set(pyproject["project"]["optional-dependencies"]["server"])
    constraints = (PACKAGE_ROOT / "constraints.txt").read_text(encoding="utf-8").splitlines()

    assert "alfworld==0.4.2" in dependencies
    assert "textworld[pddl]==1.7.0" in dependencies
    assert "numpy<2" in constraints


def test_space_image_embeds_validated_runtime_assets() -> None:
    dockerfile = (PACKAGE_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "ALFWORLD_DATA=/opt/alfworld" in dockerfile
    assert "COPY runtime-data/alfworld-runtime-assets-json-2.1.1.tar.zst" in dockerfile
    assert "COPY runtime-data/alfworld-runtime-assets-json-2.1.1.tar.zst.sha256" in dockerfile
    assert 'pip install --no-cache-dir --no-compile -c constraints.txt ".[server]"' in dockerfile
    assert r'p.write_text("\n".join(expected[:2]) + "\n")' in dockerfile
    assert "sha256sum --check" in dockerfile
    assert "tar --extract --use-compress-program=unzstd" in dockerfile
    assert "ENTRYPOINT" not in dockerfile
    assert "uvicorn alfworld_env.server.app:app" in dockerfile


def test_space_repository_excludes_local_runtime_data() -> None:
    ignored = (PACKAGE_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert "runtime-data" not in ignored
