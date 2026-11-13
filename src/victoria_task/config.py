"""Load the study settings from config.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    conditions: list[str]
    rooms: list[str]
    participants_on_run_sheet: int
    study_seconds: float
    retention_seconds: float
    block_hold_seconds: float
    grid_columns: int
    grid_rows: int
    practice_room: str
    practice_retention_seconds: float
    checks: bool
    slider_questions: list[tuple[str, str, str, str]]  # (id, question, 0 label, 100 label)
    span_start: int
    span_max: int
    span_trials: int
    span_digit_ms: int
    span_gap_ms: int

    @property
    def tiles(self) -> int:
        return self.grid_columns * self.grid_rows


def load_config(path: Path) -> Config:
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    timing, grid, practice = raw["timing"], raw.get("grid", {}), raw["practice"]
    checks = raw.get("checks", {})
    span = checks.get("digit_span", {})
    sliders = checks.get("sliders", [])
    return Config(
        conditions=list(raw["study"]["conditions"]),
        rooms=list(raw["study"]["rooms"]),
        participants_on_run_sheet=int(raw["study"]["participants_on_run_sheet"]),
        study_seconds=float(timing["study_seconds"]),
        retention_seconds=float(timing.get("retention_seconds", 0)),
        block_hold_seconds=float(timing.get("block_hold_seconds", 0)),
        grid_columns=int(grid.get("columns", 6)),
        grid_rows=int(grid.get("rows", 4)),
        practice_room=str(practice["room"]),
        practice_retention_seconds=float(practice.get("retention_seconds", 0)),
        checks=bool(checks.get("enabled", False)),
        slider_questions=[(s["id"], s["question"], s["low"], s["high"]) for s in sliders],
        span_start=int(span.get("start_length", 2)),
        span_max=int(span.get("max_length", 8)),
        span_trials=int(span.get("trials_per_length", 2)),
        span_digit_ms=int(span.get("digit_ms", 800)),
        span_gap_ms=int(span.get("gap_ms", 200)),
    )
