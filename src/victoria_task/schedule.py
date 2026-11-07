"""Deterministic assignment of condition order and room sets to a participant."""
from __future__ import annotations

from dataclasses import dataclass


def balanced_latin_square(n: int) -> list[list[int]]:
    """Return a Williams balanced Latin square for an even number of conditions.

    Each condition appears once per position, and each condition directly
    follows every other condition equally often across the rows.
    """
    if n < 1 or n % 2:
        raise ValueError("balanced_latin_square needs a positive even n")
    first: list[int] = []
    low, high = 0, n - 1
    for i in range(n):
        if i % 2 == 0:
            first.append(low)
            low += 1
        else:
            first.append(high)
            high -= 1
    return [[(value + row) % n for value in first] for row in range(n)]


@dataclass(frozen=True)
class Block:
    index: int  # 1-based position in the session
    condition: str
    rooms: tuple[str, ...]


def build_schedule(
    participant: int, conditions: list[str], room_sets: list[list[str]]
) -> list[Block]:
    """Build a participant's blocks.

    Room sets rotate independently of condition order: over n x n participants,
    every condition order is paired with every room rotation exactly once.
    """
    if participant < 1:
        raise ValueError("participant number must be 1 or higher")
    n = len(conditions)
    if len(room_sets) != n:
        raise ValueError("need exactly one room set per condition")
    square = balanced_latin_square(n)
    index = participant - 1
    order = square[index % n]
    rotation = (index // n) % n
    return [
        Block(
            index=position + 1,
            condition=conditions[condition_index],
            rooms=tuple(room_sets[(position + rotation) % n]),
        )
        for position, condition_index in enumerate(order)
    ]
