"""Deterministic assignment of condition order and room sets to a participant."""
from __future__ import annotations

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


def build_schedule(participant: int, conditions: list[str], rooms: list[str]) -> list[Block]:
    """Build a participant's blocks: one per condition, each showing every room once.

    Condition order comes from a balanced Latin square. Room order within each block
    comes from a second balanced Latin square; the row shifts with the block and with
    the participant's cycle through the condition square, so over len(square)^2
    participants every condition order meets every set of room orders.
    """
    if participant < 1:
        raise ValueError("participant number must be 1 or higher")
    condition_square = balanced_latin_square(len(conditions))
    room_square = balanced_latin_square(len(rooms))
    index = participant - 1
    order = condition_square[index % len(condition_square)]
    cycle = index // len(condition_square)
    blocks = []
    for position, condition_index in enumerate(order):
        row = room_square[(index + cycle + 2 * position) % len(room_square)]
        blocks.append(Block(index=position + 1, condition=conditions[condition_index],
                            rooms=tuple(rooms[i] for i in row)))
    return blocks
