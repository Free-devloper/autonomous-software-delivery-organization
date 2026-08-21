from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_platform_validator_accepts_phase_0d_artifacts() -> None:
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ["node", "scripts/platform.mjs", "test-platform"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "passed static security validation" in result.stdout
