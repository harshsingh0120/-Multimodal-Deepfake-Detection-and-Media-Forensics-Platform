"""Shared pytest fixtures: path setup + one-time synthetic media generation."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make `app` (backend) and `scripts` (repo root) importable regardless of cwd.
_BACKEND = Path(__file__).resolve().parents[1]
_REPO = _BACKEND.parent
for p in (str(_BACKEND), str(_REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.generate_sample_media import generate_all  # noqa: E402


@pytest.fixture(scope="session")
def samples(tmp_path_factory) -> dict[str, Path]:
    out = tmp_path_factory.mktemp("samples")
    return generate_all(out)
