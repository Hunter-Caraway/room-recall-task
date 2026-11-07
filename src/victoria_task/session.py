"""Session logic with no graphics, so it can be tested without a display.

A session is a list of steps. Each scored room is one step inside a block. All
timing comes from a clock passed in, so tests can control it.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config
from .data import ParticipantStore
from .schedule import Block, build_schedule
from .scoring import distance_pct, score


@dataclass(frozen=True)
class RoomObject:
    id: str
    label: str
    file: str
    center: tuple[float, float]
    size: tuple[int, int]


@dataclass(frozen=True)
class RoomInfo:
    name: str
    width: int
    height: int
    objects: tuple[RoomObject, ...]


def load_room(assets_dir: Path, name: str) -> RoomInfo:
    raw = json.loads((Path(assets_dir) / "rooms" / name / "room.json").read_text(encoding="utf-8"))
    objects = tuple(
        RoomObject(o["id"], o["label"], o["file"], tuple(o["center"]), tuple(o["size"]))
        for o in raw["objects"]
    )
    return RoomInfo(name, raw["width"], raw["height"], objects)


@dataclass
class Placement:
    """One object during the placement phase. Positions are room pixels."""
    obj: RoomObject
    position: tuple[float, float] | None = None
    first_placed_ms: int | None = None
    last_placed_ms: int | None = None
    placement_order: int | None = None
    moves: int = 0


@dataclass
class PlacementRound:
    room: RoomInfo
    objects: list[RoomObject]
    started_ms: int
    placements: dict[str, Placement] = field(init=False)
    _order: int = 0

    def __post_init__(self) -> None:
        self.placements = {o.id: Placement(o) for o in self.objects}

    def drop(self, object_id: str, position: tuple[float, float] | None, now_ms: int) -> None:
        """Record a drop. A position of None means it was put back in the tray."""
        placement = self.placements[object_id]
        placement.moves += 1
        if position is None:
            placement.position = None
            placement.last_placed_ms = None
            placement.placement_order = None
            return
        elapsed = now_ms - self.started_ms
        if placement.first_placed_ms is None:
            placement.first_placed_ms = elapsed
        placement.last_placed_ms = elapsed
        if placement.position is None:
            self._order += 1
            placement.placement_order = self._order
        placement.position = position

    @property
    def can_finish(self) -> bool:
        return all(p.position is not None for p in self.placements.values())


def tray_order(participant: int, block: int, room: str, objects: list[RoomObject]) -> list[RoomObject]:
    """Shuffle the tray, repeatably for a given participant and room."""
    shuffled = list(objects)
    random.Random(f"{participant}/{block}/{room}").shuffle(shuffled)
    return shuffled


class Session:
    """One participant's progress: what is next, what is saved, and how it resumes."""

    def __init__(self, config: Config, data_dir: Path, participant: int, build: str = "test"):
        self.config = config
        self.participant = participant
        self.build = build
        self.store = ParticipantStore(data_dir, participant)
        self.blocks: list[Block] = build_schedule(participant, config.conditions, config.room_sets)
        self.resumed = False
        self.finished: list[list] = []
        self.practice_done = False
        state = self.store.load_state()
        if state:
            self.resumed = True
            self.finished = state["finished"]
            self.practice_done = state["practice_done"]
            self.store.reconcile({(str(b), r) for b, r in self.finished})

    # ------------------------------------------------------------ progress
    def is_complete(self) -> bool:
        return self.store.is_complete()

    def next_room(self) -> tuple[Block, str, int] | None:
        """Return (block, room, position in block) for the first unfinished room."""
        done = {(b, r) for b, r in self.finished}
        for block in self.blocks:
            for order, room in enumerate(block.rooms, start=1):
                if (block.index, room) not in done:
                    return block, room, order
        return None

    def starts_block(self) -> bool:
        """True when the next room needs an experimenter pause: every new block
        and, after a crash, the first room back."""
        step = self.next_room()
        return step is not None and step[2] == 1

    # ------------------------------------------------------------ saving
    def _state(self, complete: bool = False) -> dict:
        return {
            "participant": self.participant,
            "practice_done": self.practice_done,
            "finished": self.finished,
            "resumed": self.resumed,
            "complete": complete,
        }

    def begin(self) -> None:
        if not self.store.has_session():
            self.store.save_state(self._state())

    def mark_practice_done(self) -> None:
        self.practice_done = True
        self.store.save_state(self._state())

    def finish_room(
        self, block: Block, order: int, placement: PlacementRound, finished_ms: int,
        study_ms: int, blink_frame_ms: float,
    ) -> list[dict]:
        rows = self._rows(block, order, placement, finished_ms, study_ms, blink_frame_ms)
        self.finished.append([block.index, placement.room.name])
        complete = self.next_room() is None
        self.store.save_room(rows, self._state(complete))
        return rows

    def _rows(self, block, order, placement, finished_ms, study_ms, blink_frame_ms) -> list[dict]:
        tolerance = self.config.tolerance_percent
        width = placement.room.width
        condition_order = ">".join(b.condition for b in self.blocks)
        room_order = ">".join("+".join(b.rooms) for b in self.blocks)
        rows = []
        for obj in placement.objects:
            item = placement.placements[obj.id]
            if item.position is None:
                raise ValueError(f"{obj.id} was not placed")
            distance = distance_pct(obj.center, item.position, width)
            rows.append({
                "participant": self.participant,
                "session_resumed": int(self.resumed),
                "block": block.index,
                "condition": block.condition,
                "room": placement.room.name,
                "room_order_in_block": order,
                "object": obj.id,
                "correct_x": f"{obj.center[0]:.1f}",
                "correct_y": f"{obj.center[1]:.1f}",
                "placed_x": f"{item.position[0]:.1f}",
                "placed_y": f"{item.position[1]:.1f}",
                "distance_pct": f"{distance:.3f}",
                "tolerance_pct": tolerance,
                "score": score(distance, tolerance),
                "placement_order": item.placement_order,
                "first_placed_ms": item.first_placed_ms,
                "last_placed_ms": item.last_placed_ms,
                "moves": item.moves,
                "room_finished_ms": finished_ms,
                "study_ms": study_ms,
                "blink_frame_ms": f"{blink_frame_ms:.1f}",
                "room_width_px": width,
                "condition_order": condition_order,
                "room_order": room_order,
                "build": self.build,
            })
        return rows
