"""Scoring for object placement. Positions are in room pixels."""
from __future__ import annotations

import math


def distance_pct(
    correct: tuple[float, float], placed: tuple[float, float], room_width: float
) -> float:
    """Distance between two points, as a percentage of the room's width."""
    return math.dist(correct, placed) / room_width * 100.0


def score(distance_percent: float, tolerance_percent: float) -> int:
    """All-or-nothing: 1 inside the tolerance (inclusive), otherwise 0."""
    return 1 if distance_percent <= tolerance_percent else 0


def nearest_other(
    object_id: str, placed: tuple[float, float], targets: dict[str, tuple[float, float]],
    room_width: float,
) -> tuple[str, float]:
    """The other target whose original spot is closest to this placement, and how far
    away it is (percent of room width). Used to score swap errors: an object put
    where a different object belonged."""
    others = [(distance_pct(spot, placed, room_width), other) for other, spot in targets.items() if other != object_id]
    distance, other = min(others)
    return other, distance


def swap(own_score: int, other_distance_percent: float, tolerance_percent: float) -> int:
    """1 when the object missed its own spot but landed on another target's spot."""
    return 1 if own_score == 0 and other_distance_percent <= tolerance_percent else 0
