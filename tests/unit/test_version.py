from __future__ import annotations

from pathlib import Path

import tomllib
import yaml

import pletopay

ROOT = Path(__file__).resolve().parent.parent.parent


def test_version_matches_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pletopay.__version__ == data["project"]["version"]


def test_api_version_matches_spec() -> None:
    spec = yaml.safe_load((ROOT / "spec" / "public.v1.yaml").read_text())
    assert str(spec["info"]["version"]) == pletopay.API_VERSION
    assert str(spec["info"]["version"]) == pletopay.Pletopay.API_VERSION
