"""Which pictures each trial shows, decided once per participant.

The participant number seeds every choice, so the same number always gets the same
deal and a resumed session continues exactly where it stopped.

  - The target photos are shared out over the scored trials, as evenly as they go
    (42 photos over 9 trials: six trials get 5 and three get 4). Each photo is a
    target once, so an earlier target never comes back in a later grid.
  - In each trial every target gets its own spot in that room, one that suits its
    size and surface.
  - Each grid is filled up with decoys. A decoy appears at most once per participant
    and is never in a room.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .schedule import Block
from .stimuli import Item, Room, Spot, overlap

PRACTICE_BLOCK = 0  # the practice trial's block number in data and state


@dataclass(frozen=True)
class Trial:
    key: str  # "1/storage"; practice is "0/practice"
    block: int
    condition: str
    room: str
    order_in_block: int
    targets: tuple[tuple[str, str], ...]  # (item name, spot id)
    grid: tuple[str, ...]  # item names in tile order, left to right then top to bottom


class DealError(RuntimeError):
    pass


def place(items: list[Item], room: Room, rng: random.Random) -> list[tuple[Item, Spot]] | None:
    """Give each item its own fitting spot, or None if the room cannot hold them.
    No two placed items may cover each other on screen, and none may cover the
    filler. Items with the fewest options go first; ties and spot choices are random."""
    options = {i.name: [s for s in room.spots if s.fits(i) and not any(overlap(s.box(i), b) for b in room.blocked)]
               for i in items}
    order = sorted(items, key=lambda i: (len(options[i.name]), rng.random()))
    chosen: dict[str, Spot] = {}
    by_name = {i.name: i for i in items}

    def solve(k: int) -> bool:
        if k == len(order):
            return True
        item = order[k]
        spots = list(options[item.name])
        rng.shuffle(spots)
        for spot in spots:
            box = spot.box(item)
            if all(s.id != spot.id and not overlap(box, s.box(placed)) for placed, s in
                   ((by_name[n], s) for n, s in chosen.items())):
                chosen[item.name] = spot
                if solve(k + 1):
                    return True
                del chosen[item.name]
        return False

    if not solve(0):
        return None
    return [(i, chosen[i.name]) for i in items]


def _grid(trial_key: str, participant: int, targets: list[Item], decoys: list[Item]) -> tuple[str, ...]:
    names = [i.name for i in targets + decoys]
    random.Random(f"grid/{participant}/{trial_key}").shuffle(names)
    return tuple(names)


def deal(participant: int, blocks: list[Block], rooms: dict[str, Room], targets: list[Item],
         decoys: list[Item], tiles: int, attempts: int = 500) -> list[Trial]:
    """The scored trials, in session order."""
    slots = [(b, r, k) for b in blocks for k, r in enumerate(b.rooms, start=1)]
    if not slots:
        return []
    rng = random.Random(f"deal/{participant}")
    base, extra = divmod(len(targets), len(slots))
    if base + (1 if extra else 0) > tiles:
        raise DealError("more targets per trial than grid tiles")
    for _ in range(attempts):
        photos = list(targets)
        rng.shuffle(photos)
        counts = [base + 1] * extra + [base] * (len(slots) - extra)
        rng.shuffle(counts)
        placed, start = [], 0
        for (block, room, _), count in zip(slots, counts):
            fit = place(photos[start:start + count], rooms[room], rng)
            if fit is None:
                break
            placed.append(fit)
            start += count
        else:
            break
    else:
        raise DealError("no deal fits the rooms' spots; add spots or check object sizes")

    pool = list(decoys)
    random.Random(f"decoys/{participant}").shuffle(pool)
    need = sum(tiles - len(p) for p in placed)
    if need > len(pool):
        raise DealError(f"need {need} decoys, only {len(pool)} exist")
    trials, used = [], 0
    for (block, room, order), fit in zip(slots, placed):
        chosen = pool[used:used + tiles - len(fit)]
        used += len(chosen)
        key = f"{block.index}/{room}"
        trials.append(Trial(
            key=key, block=block.index, condition=block.condition, room=room, order_in_block=order,
            targets=tuple((i.name, s.id) for i, s in fit),
            grid=_grid(key, participant, [i for i, _ in fit], chosen),
        ))
    return trials


def practice_trial(participant: int, room: Room, targets: list[Item], decoys: list[Item],
                   tiles: int) -> Trial:
    rng = random.Random(f"practice/{participant}")
    fit = place(list(targets), room, rng)
    if fit is None:
        raise DealError("practice objects do not fit the practice room")
    if len(targets) + len(decoys) < tiles:
        raise DealError("not enough practice decoys to fill the grid")
    chosen = list(decoys)
    rng.shuffle(chosen)
    chosen = chosen[: tiles - len(targets)]
    key = f"{PRACTICE_BLOCK}/{room.name}"
    return Trial(key=key, block=PRACTICE_BLOCK, condition="practice", room=room.name, order_in_block=1,
                 targets=tuple((i.name, s.id) for i, s in fit),
                 grid=_grid(key, participant, list(targets), chosen))
