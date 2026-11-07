"""Plays the real game loop with scripted input, using the rendered assets."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["SDL_VIDEODRIVER"] = "dummy"

from victoria_task.config import load_config
from victoria_task.selftest import check_session

ASSETS = ROOT / "assets"


@pytest.mark.skipif(not (ASSETS / "transition").exists(), reason="renders not finished")
def test_full_session_crash_and_resume(tmp_path):
    shots = ROOT / "art" / "_preview" / "shots"
    assert check_session(load_config(ROOT / "config.toml"), ASSETS, tmp_path, shots=shots) == []
