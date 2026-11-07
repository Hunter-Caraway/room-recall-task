"""Start the memory task with PsychoPy's Python: `python run_task.py` (or Run Task.bat on Windows)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from victoria_task.app import main

if __name__ == "__main__":
    sys.exit(main())
