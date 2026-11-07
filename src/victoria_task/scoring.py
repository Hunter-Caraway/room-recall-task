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
