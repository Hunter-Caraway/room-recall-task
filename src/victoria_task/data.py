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

COLUMNS = [
    "participant", "baseline", "session_resumed", "block", "condition", "room",
    "room_order_in_block", "object", "label", "correct_x", "correct_y", "placed_x", "placed_y",
    "distance_pct", "tolerance_pct", "score", "nearest_other", "nearest_other_distance_pct",
    "swap", "placement_order", "first_placed_ms", "last_placed_ms", "moves",
    "room_finished_ms", "study_ms", "study_end_frame_ms", "study_dropped_frames",
    "retention_ms", "filler_answered", "filler_correct", "room_width_px", "icon_px",
    "condition_order", "room_order", "build",
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
        self.csv_path = Path(data_dir) / f"{prefix}{participant:03d}_results.csv"
        self.state_path = Path(data_dir) / f"{prefix}{participant:03d}_state.json"

    def load_state(self) -> dict | None:
        if not self.state_path.exists():
            return None
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def is_complete(self) -> bool:
        state = self.load_state()
        return bool(state and state.get("complete"))

    def has_session(self) -> bool:
        return self.state_path.exists()

    def _read_rows(self) -> list[dict]:
        if not self.csv_path.exists():
            return []
        with open(self.csv_path, encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def save_room(self, rows: list[dict], state: dict) -> None:
        """Save one finished room. Rows go first, so a crash between the two
        writes is healed on resume by discarding rows beyond the saved state."""
        existing = self._read_rows()
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(rows)
        _atomic_write(self.csv_path, buffer.getvalue())
        self.save_state(state)

    def save_state(self, state: dict) -> None:
        _atomic_write(self.state_path, json.dumps(state, indent=2))

    def reconcile(self, finished_keys: set[tuple[str, str]]) -> None:
        """Drop rows for any (block, room) the state file does not list as finished."""
        rows = self._read_rows()
        kept = [r for r in rows if (r["block"], r["room"]) in finished_keys]
        if len(kept) == len(rows):
            return
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept)
        _atomic_write(self.csv_path, buffer.getvalue())


def run_sheet_text(
    count: int, conditions: list[str], room_sets: list[list[str]]
) -> str:
    """Experimenter-only CSV: which noise condition to set for each block."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["participant", "block", "condition", "rooms"])
    for participant in range(1, count + 1):
        blocks: list[Block] = build_schedule(participant, conditions, room_sets)
        for block in blocks:
            writer.writerow([participant, block.index, block.condition, " + ".join(block.rooms)])
    return buffer.getvalue()


def write_run_sheet(
    path: Path, count: int, conditions: list[str], room_sets: list[list[str]]
) -> None:
    _atomic_write(Path(path), run_sheet_text(count, conditions, room_sets))
