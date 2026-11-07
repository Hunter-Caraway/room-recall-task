"""Start the task. Runs under PsychoPy; see README.md.

  python run_task.py                  the real task, fullscreen
  python run_task.py --windowed       in a window, for checking
  python run_task.py --baseline       no-study guessing group (files start with B)
  python run_task.py --self-test      scripted session with no window; writes selftest.log
  python run_task.py --smoke-test     opens the window, loads every picture, closes
  python run_task.py --write-run-sheet
  python run_task.py --screenshots DIR   also save one picture of each screen (checking only)
  --config FILE, --assets DIR, --data DIR  use other files (checking only)
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from .config import load_config
from .data import write_run_sheet

ROOT = Path(__file__).resolve().parents[2]


def build_label() -> str:
    version = ROOT / "VERSION"
    return version.read_text(encoding="utf-8").strip() if version.exists() else "dev"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    def option(flag: str, default: Path) -> Path:
        return Path(argv[argv.index(flag) + 1]) if flag in argv else default

    config = load_config(option("--config", ROOT / "config.toml"))
    assets = option("--assets", ROOT / "assets")
    data_dir = option("--data", ROOT / "data")
    if "--self-test" in argv:
        from .selftest import run_self_test
        return run_self_test(assets, config, ROOT / "selftest.log")
    write_run_sheet(data_dir / "run_sheet.csv", config.participants_on_run_sheet, config.conditions, config.room_sets)
    if "--write-run-sheet" in argv:
        return 0

    from .flow import Experiment, QuitSession
    from .psychopy_display import PsychoPyDisplay

    shots = option("--screenshots", None) if "--screenshots" in argv else None
    display = PsychoPyDisplay(assets, fullscreen="--windowed" not in argv, screenshots=shots)
    experiment = Experiment(config, assets, data_dir, display, baseline="--baseline" in argv, build=build_label())
    try:
        if "--smoke-test" in argv:
            for name in experiment.all_room_names():
                experiment.room(name)
            display.transition(0.5)
            print(f"smoke test ok: {len(experiment.rooms)} rooms, {len(display.transition_frames)} "
                  f"transition frames, {display.win.size[0]}x{display.win.size[1]} screen, "
                  f"scale {display.scale:.3f}")
            return 0
        experiment.run()
    except QuitSession:
        pass
    except Exception:
        # Finished rooms are already saved. Leave the reason for the experimenter.
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "error_log.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        display.close()
    return 0
