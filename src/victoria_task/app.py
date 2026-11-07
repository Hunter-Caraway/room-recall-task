"""Start the task; see README.md.

Two displays run the same session: PsychoPy (python run_task.py, needs PsychoPy) and
pygame (python run_task.py --pygame, and always inside the single MemoryTask.exe).

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

FROZEN = getattr(sys, "frozen", False)
# Bundled files live inside the .exe; data, the log and an optional edited
# config.toml live next to it.
ROOT = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parents[2]
WRITABLE = Path(sys.executable).resolve().parent if FROZEN else ROOT


def build_label() -> str:
    version = ROOT / "VERSION"
    label = version.read_text(encoding="utf-8").strip() if version.exists() else "dev"
    return label + (" exe" if FROZEN else "")


def default_config() -> Path:
    beside = WRITABLE / "config.toml"
    return beside if beside.exists() else ROOT / "config.toml"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    def option(flag: str, default: Path) -> Path:
        return Path(argv[argv.index(flag) + 1]) if flag in argv else default

    config = load_config(option("--config", default_config()))
    assets = option("--assets", ROOT / "assets")
    data_dir = option("--data", WRITABLE / "data")
    if "--self-test" in argv:
        from .selftest import run_self_test
        return run_self_test(assets, config, WRITABLE / "selftest.log")
    write_run_sheet(data_dir / "run_sheet.csv", config.participants_on_run_sheet, config.conditions, config.room_sets)
    if "--write-run-sheet" in argv:
        return 0

    from .flow import Experiment, QuitSession

    if FROZEN or "--pygame" in argv:
        from .pygame_display import PygameDisplay as Display
    else:
        from .psychopy_display import PsychoPyDisplay as Display

    shots = option("--screenshots", None) if "--screenshots" in argv else None
    display = Display(assets, fullscreen="--windowed" not in argv, screenshots=shots)
    experiment = Experiment(config, assets, data_dir, display, baseline="--baseline" in argv, build=build_label())
    try:
        if "--smoke-test" in argv:
            for name in experiment.all_room_names():
                experiment.room(name)
            display.transition(0.5)
            print(f"smoke test ok: {len(experiment.rooms)} rooms, {len(display.transition_frames)} "
                  f"transition frames, display {type(display).__name__}")
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
