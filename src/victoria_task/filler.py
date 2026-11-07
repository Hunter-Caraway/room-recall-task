"""The filled delay between study and test: quick true-or-false sums.

Sums are verbal and numeric, with no spatial content, so they stop the participant
rehearsing the room in their head without adding spatial interference. The same
participant and block always get the same sums.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    text: str
    is_true: bool


def problems(participant: int, block: int, room: str, count: int = 200) -> list[Problem]:
    rng = random.Random(f"filler/{participant}/{block}/{room}")
    result = []
    for _ in range(count):
        a, b = rng.randint(2, 19), rng.randint(2, 19)
        if rng.random() < 0.5:
            op, answer = "+", a + b
        else:
            a, b = max(a, b), min(a, b)
            op, answer = "-", a - b
        is_true = rng.random() < 0.5
        shown = answer if is_true else answer + rng.choice([-2, -1, 1, 2])
        result.append(Problem(f"{a} {op} {b} = {shown}", is_true))
    return result


@dataclass
class FillerResult:
    answered: int = 0
    correct: int = 0
