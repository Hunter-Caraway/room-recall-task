"""Load the study settings from config.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    conditions: list[str]
    room_sets: list[list[str]]
    study_seconds: float
    retention_seconds: float
    tolerance_percent: float
    transition_seconds: float
    practice_room: str
    practice_objects: int
    practice_retention_seconds: float
    participants_on_run_sheet: int


def load_config(path: Path) -> Config:
    with open(path, "rb") as handle:
        raw = tomllib.load(handle)
    return Config(
        conditions=list(raw["study"]["conditions"]),
        room_sets=[list(room_set) for room_set in raw["study"]["room_sets"]],
        study_seconds=float(raw["timing"]["study_seconds"]),
        retention_seconds=float(raw["timing"].get("retention_seconds", 0)),
        tolerance_percent=float(raw["scoring"]["tolerance_percent"]),
        transition_seconds=float(raw["timing"]["transition_seconds"]),
        practice_room=str(raw["practice"]["room"]),
        practice_objects=int(raw["practice"]["objects"]),
        practice_retention_seconds=float(raw["practice"].get("retention_seconds", 0)),
        participants_on_run_sheet=int(raw["study"]["participants_on_run_sheet"]),
    )
