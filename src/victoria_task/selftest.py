"""Play whole scripted sessions with no window and check what got saved.

Uses the real session flow (flow.py), drag-and-drop logic (layout.py) and data
files, with a scripted display in place of PsychoPy. Run it on the lab computer
with `Self Test.bat` or `python run_task.py --self-test`; it writes selftest.log.
Real display and mouse behaviour still need a person at the lab computer.
"""
from __future__ import annotations

import csv
import dataclasses
import itertools
import math
import tempfile
import traceback
from pathlib import Path

from .config import Config
from .filler import FillerResult
from .flow import PAUSE_TEXT, Experiment, QuitSession
from .layout import DONE_RECT, ICON_PX, PlacementController, load_icon, to_canvas
from .session import Session, load_room

DONE_POINT = (DONE_RECT[0] + DONE_RECT[2] / 2, DONE_RECT[1] + DONE_RECT[3] / 2)


def solid_point(controller: PlacementController, object_id: str) -> tuple[float, float]:
    """A canvas point on a solid pixel of a placed object, nearest its centre."""
    icon = controller.icons[object_id]
    cx, cy = controller.placed_centre(object_id)
    w, h = icon.size
    best = min(
        ((c, r) for r in range(h) for c in range(w) if icon.solid[r][c]),
        key=lambda p: (p[0] - w / 2) ** 2 + (p[1] - h / 2) ** 2,
    )
    return cx - w / 2 + best[0] + 0.5, cy - h / 2 + best[1] + 0.5


class ScriptedDisplay:
    """Answers every screen automatically and records the text shown."""

    def __init__(self, participant: int):
        self.participant = participant
        self.clock = itertools.count(0, 16)
        self.shown: list[str] = []
        self.prepared: list[str] = []
        self.transitions = 0

    def now_ms(self) -> int:
        return next(self.clock)

    def message(self, lines, key):
        self.shown += [text for text, _ in lines]

    def enter_participant(self):
        return self.participant

    def ask_resume(self, number):
        return True

    def prepare(self, room, icons):
        self.prepared.append(room.name)

    def study(self, room, seconds, cut_to_empty):
        return int(seconds * 1000), 16.7, 0

    def filler(self, items, seconds):
        # Answer five sums, getting the last one wrong.
        answers = [p.is_true for p in items[:4]] + [not items[4].is_true]
        return FillerResult(answered=5, correct=sum(a == p.is_true for a, p in zip(answers, items)))

    def placement(self, room, controller: PlacementController):
        full_round = len(controller.order) == len(room.objects)
        assert not controller.press(DONE_POINT, self.now_ms()), "Done worked before all objects were placed"
        order = controller.order
        for index, obj in enumerate(order):
            start = controller.slots[obj.id]
            target = to_canvas(obj.center)
            if full_round and index == 0:  # dropped just outside tolerance: must score 0
                shift = room.width * 0.0505
                target = (target[0] + (shift if obj.center[0] < room.width / 2 else -shift), target[1])
            if full_round and index == 2:  # dropped on the next object's spot: a swap error
                target = to_canvas(order[3].center)
            if full_round and index == 1:  # back to the tray first, then placed properly
                controller.press(start, self.now_ms())
                controller.release((start[0], start[1] - 5), self.now_ms())
            controller.press(start, self.now_ms())
            controller.move(target)
            controller.release(target, self.now_ms())
            if full_round and index == 4:  # picked up again in the room and put back: 2 moves
                grab = solid_point(controller, obj.id)
                controller.press(grab, self.now_ms())
                offset = (grab[0] - target[0], grab[1] - target[1])
                fixed = to_canvas(obj.center)
                controller.move((fixed[0] + offset[0], fixed[1] + offset[1]))
                controller.release((fixed[0] + offset[0], fixed[1] + offset[1]), self.now_ms())
        assert controller.press(DONE_POINT, self.now_ms()), "Done did not finish a complete room"

    def transition(self, seconds):
        self.transitions += 1


class _StopHere(QuitSession):
    pass


def play(config: Config, assets: Path, data_dir: Path, participant: int, crash_after_room=False,
         baseline=False) -> ScriptedDisplay:
    display = ScriptedDisplay(participant)
    experiment = Experiment(config, assets, data_dir, display, baseline=baseline, build="selftest")
    if not crash_after_room:
        experiment.run()
        return display
    original = Session.finish_room

    def stop_after_save(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise _StopHere

    Session.finish_room = stop_after_save
    try:
        experiment.run()
    except _StopHere:
        pass
    finally:
        Session.finish_room = original
    return display


def read_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_assets(config: Config, assets: Path) -> list[str]:
    """The pictures must not give locations away and targets must not overlap."""
    failures = []
    names = [config.practice_room] + [n for s in config.room_sets for n in s]
    labels: dict[str, str] = {}
    for name in dict.fromkeys(names):
        info = load_room(assets, name)
        if len(info.objects) < (config.practice_objects if name == config.practice_room else 15):
            failures.append(f"{name}: only {len(info.objects)} objects")
        limit = 2 * config.tolerance_percent / 100 * info.width
        for a, b in itertools.combinations(info.objects, 2):
            if math.dist(a.center, b.center) < limit:
                failures.append(f"{name}: {a.id} and {b.id} closer than twice the tolerance")
        for obj in info.objects:
            if not obj.icon.startswith("icons/"):
                failures.append(f"{name}/{obj.id}: icon is not a separate neutral render")
            icon = load_icon(assets / "rooms" / name / obj.icon)
            if max(icon.size) != ICON_PX:
                failures.append(f"{name}/{obj.id}: icon drawn at {icon.size}")
            if obj.label in labels:
                failures.append(f"{name}/{obj.id}: label '{obj.label}' also used in {labels[obj.label]}")
            labels[obj.label] = name
    return failures


def check_session(config: Config, assets: Path, data_dir: Path) -> list[str]:
    """Return a list of failures. An empty list means everything worked."""
    failures = check_assets(config, assets)

    def expect(condition, message):
        if not condition:
            failures.append(message)

    expected_rooms = sum(len(rooms) for rooms in config.room_sets)

    # An uninterrupted session.
    display = play(config, assets, data_dir, 1)
    rows = read_rows(data_dir / "P001_results.csv")
    expect(len(rows) == 15 * expected_rooms, f"expected {15 * expected_rooms} rows, got {len(rows)}")
    expect({r["session_resumed"] for r in rows} == {"0"}, "uninterrupted session marked as resumed")
    expect({r["condition"] for r in rows} == set(config.conditions), "not all conditions recorded")
    per_room: dict[str, int] = {}
    swaps: dict[str, int] = {}
    for row in rows:
        per_room[row["room"]] = per_room.get(row["room"], 0) + int(row["score"])
        swaps[row["room"]] = swaps.get(row["room"], 0) + int(row["swap"])
    expect(all(v == 13 for v in per_room.values()), f"each room should score 13/15, got {per_room}")
    expect(all(v == 1 for v in swaps.values()), f"each room should have 1 swap, got {swaps}")
    twice = [r for r in rows if r["moves"] == "2"]
    expect(len(twice) == 2 * expected_rooms, f"moves not counted: {len(twice)} rows with 2 moves")
    expect(all(r["moves"] in ("1", "2") for r in rows), "unexpected move count")
    expect(all(r["placement_order"] for r in rows), "missing placement order")
    expect(all(r["filler_answered"] == "5" and r["filler_correct"] == "4" for r in rows)
           or config.retention_seconds <= 0, "filler results not saved")
    expect(display.transitions == expected_rooms, f"{display.transitions} transitions shown")

    # Nothing shown on any screen may reveal a condition.
    shown = display.shown
    leaks = [t for t in shown if t in set(config.conditions) or "condition" in t.lower()]
    expect(not leaks, f"condition shown on screen: {leaks}")
    expect(PAUSE_TEXT in shown, "experimenter pause was not shown")
    header = set(rows[0])
    expect(not {"name", "email", "birthdate", "age"} & header, "personal detail column in results")

    # Crash after the first room, then resume.
    play(config, assets, data_dir, 2, crash_after_room=True)
    first = read_rows(data_dir / "P002_results.csv")
    expect(len(first) == 15, f"crash should leave 15 saved rows, got {len(first)}")
    expect(not Session(config, data_dir, 2).is_complete(), "crashed session reported as complete")
    play(config, assets, data_dir, 2)
    final = read_rows(data_dir / "P002_results.csv")
    expect(len(final) == 15 * expected_rooms, f"resume left {len(final)} rows")
    expect(len({(r["block"], r["room"], r["object"]) for r in final}) == len(final), "resume duplicated rows")
    expect(any(r["session_resumed"] == "1" for r in final), "resumed rows are not marked")
    expect(Session(config, data_dir, 2).is_complete(), "resumed session not marked complete")
    before = (data_dir / "P002_results.csv").read_bytes()
    Session(config, data_dir, 2)
    expect((data_dir / "P002_results.csv").read_bytes() == before, "reopening changed finished data")

    # The no-study baseline group: separate files, no study, no pause, no condition.
    display = play(config, assets, data_dir, 3, baseline=True)
    base = read_rows(data_dir / "B003_results.csv")
    expect(len(base) == 15 * expected_rooms, f"baseline wrote {len(base)} rows")
    expect({r["condition"] for r in base} == {"baseline"}, "baseline rows carry a condition")
    expect({r["study_ms"] for r in base} == {"0"}, "baseline participants saw the study room")
    expect(PAUSE_TEXT not in display.shown, "baseline session paused for noise")
    expect(not (data_dir / "P003_results.csv").exists(), "baseline wrote a participant file")
    return failures


def run_self_test(assets: Path, config: Config, log_path: Path) -> int:
    try:
        with tempfile.TemporaryDirectory() as temp:
            failures = check_session(config, assets, Path(temp))
    except Exception:
        failures = [traceback.format_exc()]
    text = "SELF TEST PASSED\n" if not failures else "SELF TEST FAILED\n" + "\n".join(failures) + "\n"
    log_path.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not failures else 1
