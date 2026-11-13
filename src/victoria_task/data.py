"""Per-participant results, autosave and experimenter run sheets.

Files contain participant numbers only, never names or other personal details.
Every write goes through a temp file and rename, so a crash cannot leave a
half-written CSV.
"""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from .schedule import Block, build_schedule

# One row per grid tile.
TILE_COLUMNS = [
    "participant", "baseline", "session_resumed", "block", "condition", "room", "room_order_in_block",
    "tile", "item", "label", "category", "role", "spot", "rotate_deg", "selected", "correct",
    "first_selected_ms", "last_toggle_ms", "toggles", "build",
]
# One row per trial (room).
TRIAL_COLUMNS = [
    "participant", "baseline", "session_resumed", "block", "condition", "room", "room_order_in_block",
    "targets", "decoys", "hits", "false_alarms", "hit_rate", "false_alarm_rate", "dprime", "criterion",
    "selected", "grid_ms", "study_ms", "study_end_frame_ms", "study_dropped_frames", "retention_ms",
    "filler_answered", "filler_correct", "filler_mean_rt_ms", "condition_order", "room_order", "build",
]

# Manipulation checks after each block: one row per digit-span trial, per span
# score and per slider.
CHECK_COLUMNS = [
    "participant", "session_resumed", "block", "condition", "measure", "trial", "length",
    "sequence", "response", "correct", "value", "first_click_ms", "rt_ms", "build",
]


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


class ParticipantStore:
    def __init__(self, data_dir: Path, participant: int, prefix: str = "P"):
        """prefix is "P" for participants and "B" for the no-study baseline group."""
        self.participant = participant
        self.tiles_path = Path(data_dir) / f"{prefix}{participant:03d}_tiles.csv"
        self.trials_path = Path(data_dir) / f"{prefix}{participant:03d}_trials.csv"
        self.state_path = Path(data_dir) / f"{prefix}{participant:03d}_state.json"
        self.checks_path = Path(data_dir) / f"{prefix}{participant:03d}_checks.csv"

    def load_state(self) -> dict | None:
        if not self.state_path.exists():
            return None
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def is_complete(self) -> bool:
        state = self.load_state()
        return bool(state and state.get("complete"))

    def has_session(self) -> bool:
        return self.state_path.exists()

    @staticmethod
    def _read(path: Path) -> list[dict]:
        if not path.exists():
            return []
        with open(path, encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _write(path: Path, columns: list[str], rows: list[dict]) -> None:
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        _atomic_write(path, buffer.getvalue())

    def save_trial(self, tile_rows: list[dict], trial_row: dict, state: dict) -> None:
        """Save one finished trial. Rows go first, so a crash between the writes is
        healed on resume by dropping rows the state file does not list as finished."""
        self._write(self.tiles_path, TILE_COLUMNS, self._read(self.tiles_path) + tile_rows)
        self._write(self.trials_path, TRIAL_COLUMNS, self._read(self.trials_path) + [trial_row])
        self.save_state(state)

    def save_checks(self, rows: list[dict], state: dict) -> None:
        """Save one block's manipulation checks, rows first as in save_room."""
        self._write(self.checks_path, CHECK_COLUMNS, self._read(self.checks_path) + rows)
        self.save_state(state)

    def save_state(self, state: dict) -> None:
        _atomic_write(self.state_path, json.dumps(state, indent=2))

    def reconcile(self, finished_keys: set[tuple[str, str]], checked_blocks: set[str] = frozenset()) -> None:
        """Drop rows for any (block, room), or block of checks, the state file does
        not list as finished."""
        for path, columns in ((self.tiles_path, TILE_COLUMNS), (self.trials_path, TRIAL_COLUMNS)):
            rows = self._read(path)
            kept = [r for r in rows if (r["block"], r["room"]) in finished_keys]
            if len(kept) != len(rows):
                self._write(path, columns, kept)
        checks = self._read(self.checks_path)
        kept = [r for r in checks if r["block"] in checked_blocks]
        if len(kept) != len(checks):
            self._write(self.checks_path, CHECK_COLUMNS, kept)


def run_sheet_text(count: int, conditions: list[str], rooms: list[str]) -> str:
    """Experimenter-only CSV: which noise condition to set for each block."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["participant", "block", "condition", "rooms"])
    for participant in range(1, count + 1):
        blocks: list[Block] = build_schedule(participant, conditions, rooms)
        for block in blocks:
            writer.writerow([participant, block.index, block.condition, " + ".join(block.rooms)])
    return buffer.getvalue()


def write_run_sheet(path: Path, count: int, conditions: list[str], rooms: list[str]) -> None:
    _atomic_write(Path(path), run_sheet_text(count, conditions, rooms))
