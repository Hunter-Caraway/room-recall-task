"""Deterministic assignment of condition order and room sets to a participant."""
from __future__ import annotations

import random
from dataclasses import dataclass


def balanced_latin_square(n: int) -> list[list[int]]:
    """Return a Williams balanced Latin square.

    Each condition appears equally often in each position, and each condition
    directly follows every other condition equally often across the rows. An
    even n needs n rows. An odd n needs 2n rows: the square plus each row reversed.
    """
    if n < 1:
        raise ValueError("balanced_latin_square needs at least one condition")
    first: list[int] = []
    low, high = 0, n - 1
    for i in range(n):
        if i % 2 == 0:
            first.append(low)
            low += 1
        else:
            first.append(high)
            high -= 1
    square = [[(value + row) % n for value in first] for row in range(n)]
    if n % 2:
        square += [list(reversed(row)) for row in square]
    return square


@dataclass(frozen=True)
class Block:
    index: int  # 1-based position in the session
    condition: str
    rooms: tuple[str, ...]


def build_schedule(
    participant: int, conditions: list[str], room_sets: list[list[str]]
) -> list[Block]:
    """Build a participant's blocks.

    Room sets rotate independently of condition order: over len(square) x n
    participants, every condition order is paired with every room-set rotation
    exactly once. Within a block the room order is shuffled, repeatably for a
    given participant, so no room type always comes first.
    """
    if participant < 1:
        raise ValueError("participant number must be 1 or higher")
    n = len(conditions)
    if len(room_sets) != n:
        raise ValueError("need exactly one room set per condition")
    square = balanced_latin_square(n)
    index = participant - 1
    order = square[index % len(square)]
    rotation = (index // len(square)) % n
    blocks = []
    for position, condition_index in enumerate(order):
        rooms = list(room_sets[(position + rotation) % n])
        random.Random(f"rooms/{participant}/{position + 1}").shuffle(rooms)
        blocks.append(Block(index=position + 1, condition=conditions[condition_index], rooms=tuple(rooms)))
    return blocks
