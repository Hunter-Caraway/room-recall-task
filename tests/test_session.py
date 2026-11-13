"""Plays the real session flow with a scripted display."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import fake_assets
from victoria_task.config import load_config
from victoria_task.selftest import check_session

ASSETS = ROOT / "assets"


def test_full_session_on_synthetic_assets(tmp_path):
    assets = fake_assets.make(tmp_path / "assets")
    assert check_session(load_config(ROOT / "config.toml"), assets, tmp_path / "data") == []


@pytest.mark.skipif(not (ASSETS / "objects" / "drawings").exists(), reason="drawings not built (art/build_drawn.py)")
def test_full_session_on_real_assets(tmp_path):
    assert check_session(load_config(ROOT / "config.toml"), ASSETS, tmp_path) == []
