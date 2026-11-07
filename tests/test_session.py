"""Plays the real session flow with a scripted display, using the rendered assets."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from victoria_task.config import load_config
from victoria_task.selftest import check_session

ASSETS = ROOT / "assets"


@pytest.mark.skipif(not (ASSETS / "transition").exists(), reason="renders not finished")
def test_full_session_crash_resume_and_baseline(tmp_path):
    assert check_session(load_config(ROOT / "config.toml"), ASSETS, tmp_path) == []
