"""Load the study settings from config.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    conditions: list[str]
    room_sets: list[list[str]]
    objects_per_room: int
    study_seconds: float
    retention_seconds: float
    tolerance_percent: float
    transition_seconds: float
    practice_rooms: list[str]
    practice_objects: int
    practice_retention_seconds: float
    participants_on_run_sheet: int
    checks: bool
    slider_questions: list[tuple[str, str, str, str]]  # (id, question, 0 label, 100 label)
    span_start: int
    span_max: int
    span_trials: int
    span_digit_ms: int
    span_gap_ms: int

    def practice_room(self, block_index: int) -> str:
        """The practice room that opens a block (block_index is 1-based)."""
        return self.practice_rooms[(block_index - 1) % len(self.practice_rooms)]


def load_config(path: Path) -> Config:
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    practice = raw["practice"]
    rooms = practice.get("rooms") or [practice["room"]]
    checks = raw.get("checks", {})
    span = checks.get("digit_span", {})
    sliders = checks.get("sliders", [])
    return Config(
        conditions=list(raw["study"]["conditions"]),
        room_sets=[list(room_set) for room_set in raw["study"]["room_sets"]],
        objects_per_room=int(raw["study"].get("objects_per_room", 6)),
        study_seconds=float(raw["timing"]["study_seconds"]),
        retention_seconds=float(raw["timing"].get("retention_seconds", 0)),
        tolerance_percent=float(raw["scoring"]["tolerance_percent"]),
        transition_seconds=float(raw["timing"]["transition_seconds"]),
        practice_rooms=[str(r) for r in rooms],
        practice_objects=int(practice["objects"]),
        practice_retention_seconds=float(practice.get("retention_seconds", 0)),
        participants_on_run_sheet=int(raw["study"]["participants_on_run_sheet"]),
        checks=bool(checks.get("enabled", False)),
        slider_questions=[(s["id"], s["question"], s["low"], s["high"]) for s in sliders],
        span_start=int(span.get("start_length", 2)),
        span_max=int(span.get("max_length", 8)),
        span_trials=int(span.get("trials_per_length", 2)),
        span_digit_ms=int(span.get("digit_ms", 800)),
        span_gap_ms=int(span.get("gap_ms", 200)),
    )
