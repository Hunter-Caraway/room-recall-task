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
from .scoring import distance_pct, nearest_other, score, swap


@dataclass(frozen=True)
class RoomObject:
    id: str
    label: str
    file: str
    center: tuple[float, float]
    size: tuple[int, int]
    icon: str  # neutral picture shown in the tray and when placed; never cut from the room


@dataclass(frozen=True)
class RoomInfo:
    name: str
    width: int
    height: int
    objects: tuple[RoomObject, ...]


def load_room(assets_dir: Path, name: str) -> RoomInfo:
    raw = json.loads((Path(assets_dir) / "rooms" / name / "room.json").read_text(encoding="utf-8"))
    objects = tuple(
        RoomObject(o["id"], o["label"], o["file"], tuple(o["center"]), tuple(o["size"]), o["icon"])
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
    first_pickup_ms: int | None = None  # first time it was picked up from the tray
    held_ms: int = 0  # total time spent dragging it
    correction_ms: int = 0  # time spent dragging it after its first placement
    _picked_at: int | None = None
    _correcting: bool = False


@dataclass
class PlacementRound:
    room: RoomInfo
    objects: list[RoomObject]
    started_ms: int
    placements: dict[str, Placement] = field(init=False)
    _order: int = 0

    def __post_init__(self) -> None:
        self.placements = {o.id: Placement(o) for o in self.objects}

    def pick_up(self, object_id: str, now_ms: int) -> None:
        """Record the start of a drag, from the tray or from the room."""
        placement = self.placements[object_id]
        elapsed = now_ms - self.started_ms
        if placement.first_pickup_ms is None:
            placement.first_pickup_ms = elapsed
        placement._picked_at = now_ms
        placement._correcting = placement.first_placed_ms is not None

    def drop(self, object_id: str, position: tuple[float, float] | None, now_ms: int) -> None:
        """Record a drop. A position of None means it was put back in the tray."""
        placement = self.placements[object_id]
        placement.moves += 1
        if placement._picked_at is not None:
            held = now_ms - placement._picked_at
            placement.held_ms += held
            if placement._correcting:
                placement.correction_ms += held
            placement._picked_at = None
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


@dataclass
class RoomTiming:
    """What the display measured for one scored room."""
    finished_ms: int
    study_ms: int
    study_end_frame_ms: float
    study_dropped_frames: int | None
    retention_ms: int
    filler_answered: int
    filler_correct: int
    icon_px: int
    filler_mean_rt_ms: float | None = None


class Session:
    """One participant's progress: what is next, what is saved, and how it resumes.

    Each block is: a practice room (not saved), its scored rooms, then the
    manipulation checks. baseline=True is the no-study group: they never see the
    full rooms, so their placements measure how far objects can be placed by
    guessing alone. Their files start with B instead of P, their condition is
    recorded as baseline, they practise only before block 1 and have no checks.
    """

    def __init__(
        self, config: Config, data_dir: Path, participant: int, build: str = "test",
        baseline: bool = False,
    ):
        self.config = config
        self.participant = participant
        self.build = build
        self.baseline = baseline
        self.store = ParticipantStore(data_dir, participant, "B" if baseline else "P")
        self.blocks: list[Block] = build_schedule(participant, config.conditions, config.room_sets)
        self.resumed = False
        self.finished: list[list] = []
        self.practice_done: list[int] = []
        self.checks_done: list[int] = []
        state = self.store.load_state()
        if state:
            self.resumed = True
            self.finished = state["finished"]
            self.practice_done = list(state.get("practice_done", []))
            self.checks_done = list(state.get("checks_done", []))
            self.store.reconcile({(str(b), r) for b, r in self.finished}, {str(b) for b in self.checks_done})

    # ------------------------------------------------------------ progress
    def is_complete(self) -> bool:
        return self.store.is_complete()

    def _all_done(self) -> bool:
        return all(not self.rooms_left(b) and not self.needs_checks(b) for b in self.blocks)

    def rooms_left(self, block: Block) -> list[tuple[str, int]]:
        """(room, position in block) for each unfinished room in the block."""
        done = {(b, r) for b, r in self.finished}
        return [(room, order) for order, room in enumerate(block.rooms, start=1)
                if (block.index, room) not in done]

    def needs_practice(self, block: Block) -> bool:
        """Practice opens a block, unless a room of it is already done (a resumed
        session) or this is a baseline session past block 1."""
        if block.index in self.practice_done or len(self.rooms_left(block)) < len(block.rooms):
            return False
        return not (self.baseline and block.index > 1)

    def needs_checks(self, block: Block) -> bool:
        return self.config.checks and not self.baseline and block.index not in self.checks_done

    # ------------------------------------------------------------ saving
    def _state(self) -> dict:
        return {
            "participant": self.participant,
            "practice_done": self.practice_done,
            "finished": self.finished,
            "checks_done": self.checks_done,
            "resumed": self.resumed,
            "complete": self._all_done(),
        }

    def begin(self) -> None:
        if not self.store.has_session():
            self.store.save_state(self._state())

    def mark_practice_done(self, block: Block) -> None:
        self.practice_done.append(block.index)
        self.store.save_state(self._state())

    def finish_room(
        self, block: Block, order: int, placement: PlacementRound, timing: RoomTiming,
    ) -> list[dict]:
        rows = self._rows(block, order, placement, timing)
        self.finished.append([block.index, placement.room.name])
        self.store.save_room(rows, self._state())
        return rows

    def finish_checks(self, block: Block, rows: list[dict]) -> None:
        self.checks_done.append(block.index)
        self.store.save_checks(rows, self._state())

    def condition(self, block: Block) -> str:
        return "baseline" if self.baseline else block.condition

    def check_base(self, block: Block) -> dict:
        """The columns every manipulation-check row starts with."""
        return {"participant": self.participant, "session_resumed": int(self.resumed),
                "block": block.index, "condition": self.condition(block), "build": self.build}

    def _rows(self, block: Block, order: int, placement: PlacementRound, timing: RoomTiming) -> list[dict]:
        tolerance = self.config.tolerance_percent
        width = placement.room.width
        targets = {o.id: o.center for o in placement.objects}
        condition_order = ">".join(self.condition(b) for b in self.blocks)
        room_order = ">".join("+".join(b.rooms) for b in self.blocks)
        # Placement latency: time from the previous object's first placement (or
        # from the empty room appearing) to this object's first placement.
        by_time = sorted(placement.placements.values(), key=lambda p: (p.first_placed_ms, p.obj.id))
        latency_of = {p.obj.id: p.first_placed_ms - (by_time[i - 1].first_placed_ms if i else 0)
                      for i, p in enumerate(by_time)}
        rows = []
        for obj in placement.objects:
            item = placement.placements[obj.id]
            if item.position is None:
                raise ValueError(f"{obj.id} was not placed")
            distance = distance_pct(obj.center, item.position, width)
            own = score(distance, tolerance)
            other, other_distance = nearest_other(obj.id, item.position, targets, width)
            rows.append({
                "participant": self.participant,
                "baseline": int(self.baseline),
                "session_resumed": int(self.resumed),
                "block": block.index,
                "condition": self.condition(block),
                "room": placement.room.name,
                "room_order_in_block": order,
                "object": obj.id,
                "label": obj.label,
                "correct_x": f"{obj.center[0]:.1f}",
                "correct_y": f"{obj.center[1]:.1f}",
                "placed_x": f"{item.position[0]:.1f}",
                "placed_y": f"{item.position[1]:.1f}",
                "distance_pct": f"{distance:.3f}",
                "distance_px": f"{distance * width / 100:.1f}",
                "tolerance_pct": tolerance,
                "score": own,
                "nearest_other": other,
                "nearest_other_distance_pct": f"{other_distance:.3f}",
                "swap": swap(own, other_distance, tolerance),
                "placement_order": item.placement_order,
                "first_pickup_ms": item.first_pickup_ms,
                "first_placed_ms": item.first_placed_ms,
                "placement_latency_ms": latency_of[obj.id],
                "last_placed_ms": item.last_placed_ms,
                "held_ms": item.held_ms,
                "correction_ms": item.correction_ms,
                "moves": item.moves,
                "reconstruction_ms": timing.finished_ms,
                "study_ms": timing.study_ms,
                "study_end_frame_ms": f"{timing.study_end_frame_ms:.1f}",
                "study_dropped_frames": "" if timing.study_dropped_frames is None else timing.study_dropped_frames,
                "retention_ms": timing.retention_ms,
                "filler_answered": timing.filler_answered,
                "filler_correct": timing.filler_correct,
                "filler_mean_rt_ms": "" if timing.filler_mean_rt_ms is None else f"{timing.filler_mean_rt_ms:.0f}",
                "room_width_px": width,
                "icon_px": timing.icon_px,
                "condition_order": condition_order,
                "room_order": room_order,
                "build": self.build,
            })
        return rows
