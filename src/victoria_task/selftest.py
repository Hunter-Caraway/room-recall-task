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

from .checks import CONTINUE_RECT, SLIDER_Y, SliderController
from .config import Config
from .filler import FillerResult
from .flow import Experiment, QuitSession
from .layout import DONE_RECT, ICON_PX, PlacementController, load_icon, to_canvas
from .session import Session, load_room

DONE_POINT = (DONE_RECT[0] + DONE_RECT[2] / 2, DONE_RECT[1] + DONE_RECT[3] / 2)
CONTINUE_POINT = (CONTINUE_RECT[0] + CONTINUE_RECT[2] / 2, CONTINUE_RECT[1] + CONTINUE_RECT[3] / 2)
SPAN_RIGHT_UP_TO = 4  # the script answers digit-span trials right up to this length
SLIDER_ANSWER = 65
PAUSE_TEXT = "Please wait for the experimenter"  # removed from the task; must never appear


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
        result = FillerResult()
        for said, problem in zip(answers, items):
            result.answer(problem, said, 900)
        return result

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

    def digit_span(self, digits, digit_ms, gap_ms):
        backward = "".join(str(d) for d in reversed(digits))
        return (backward if len(digits) <= SPAN_RIGHT_UP_TO else backward[::-1]), 1500

    def slider(self, question, low, high, controller: SliderController):
        self.shown.append(question)
        assert not controller.press(CONTINUE_POINT, self.now_ms()), "Continue worked before an answer"
        controller.press((SliderController.x_for(40), SLIDER_Y + 10), self.now_ms())
        controller.move((SliderController.x_for(SLIDER_ANSWER), SLIDER_Y + 200), self.now_ms())
        controller.release((SliderController.x_for(SLIDER_ANSWER), SLIDER_Y + 200), self.now_ms())
        assert controller.press(CONTINUE_POINT, self.now_ms()), "Continue did not accept an answer"


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
    names = config.practice_rooms + [n for s in config.room_sets for n in s]
    labels: dict[str, str] = {}  # label -> room type
    spots: dict[tuple[str, str], list[tuple[str, tuple[float, float]]]] = {}  # (type, object) -> (room, spot)
    for name in dict.fromkeys(names):
        info = load_room(assets, name)
        kind = room_type(name)
        practice = name in config.practice_rooms
        if practice and len(info.objects) < config.practice_objects:
            failures.append(f"{name}: only {len(info.objects)} objects")
        if not practice and len(info.objects) != config.objects_per_room:
            failures.append(f"{name}: {len(info.objects)} objects, config says {config.objects_per_room}")
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
            if labels.get(obj.label, kind) != kind:
                failures.append(f"{name}/{obj.id}: label '{obj.label}' also used in a {labels[obj.label]}")
            labels[obj.label] = kind
            spots.setdefault((kind, obj.id), []).append((name, obj.center))
    # Objects switch places between arrangements: the same object must never be
    # within twice the tolerance of where it stood in another arrangement.
    for (kind, object_id), seen in spots.items():
        for (room_a, a), (room_b, b) in itertools.combinations(seen, 2):
            width = load_room(assets, room_a).width
            if math.dist(a, b) < 2 * config.tolerance_percent / 100 * width:
                failures.append(f"{object_id}: same place in {room_a} and {room_b}")
    return failures


def room_type(name: str) -> str:
    """bedroom_2 -> bedroom. Arrangements of one room share a type."""
    stem, _, suffix = name.rpartition("_")
    return stem if suffix.isdigit() else name


def check_session(config: Config, assets: Path, data_dir: Path) -> list[str]:
    """Return a list of failures. An empty list means everything worked."""
    failures = check_assets(config, assets)

    def expect(condition, message):
        if not condition:
            failures.append(message)

    n = config.objects_per_room
    expected_rooms = sum(len(rooms) for rooms in config.room_sets)
    blocks = len(config.conditions)

    # An uninterrupted session.
    display = play(config, assets, data_dir, 1)
    rows = read_rows(data_dir / "P001_results.csv")
    expect(len(rows) == n * expected_rooms, f"expected {n * expected_rooms} rows, got {len(rows)}")
    expect({r["session_resumed"] for r in rows} == {"0"}, "uninterrupted session marked as resumed")
    expect({r["condition"] for r in rows} == set(config.conditions), "not all conditions recorded")
    per_room: dict[str, int] = {}
    swaps: dict[str, int] = {}
    for row in rows:
        per_room[row["room"]] = per_room.get(row["room"], 0) + int(row["score"])
        swaps[row["room"]] = swaps.get(row["room"], 0) + int(row["swap"])
    expect(all(v == n - 2 for v in per_room.values()), f"each room should score {n - 2}/{n}, got {per_room}")
    expect(all(v == 1 for v in swaps.values()), f"each room should have 1 swap, got {swaps}")
    twice = [r for r in rows if r["moves"] == "2"]
    expect(len(twice) == 2 * expected_rooms, f"moves not counted: {len(twice)} rows with 2 moves")
    expect(all(r["moves"] in ("1", "2") for r in rows), "unexpected move count")
    expect(all(r["placement_order"] for r in rows), "missing placement order")
    expect(all(r["filler_answered"] == "5" and r["filler_correct"] == "4" and r["filler_mean_rt_ms"] == "900"
               for r in rows) or config.retention_seconds <= 0, "filler results not saved")
    # Response times: every object has them, and only the object moved again in the
    # room has correction time.
    for column in ("first_pickup_ms", "first_placed_ms", "placement_latency_ms", "held_ms", "reconstruction_ms"):
        expect(all(r[column] != "" and int(r[column]) >= 0 for r in rows), f"{column} missing")
    corrected = [r for r in rows if int(r["correction_ms"]) > 0]
    expect(len(corrected) == expected_rooms, f"{len(corrected)} rows with correction time")
    for room in {r["room"] for r in rows}:
        mine = [r for r in rows if r["room"] == room]
        last = max(int(r["first_placed_ms"]) for r in mine)
        expect(sum(int(r["placement_latency_ms"]) for r in mine) == last,
               f"{room}: placement latencies do not add up to the last first placement")
    used = {config.practice_room(b) for b in range(1, blocks + 1)}
    expect(used <= set(display.prepared), "a block's practice room was not shown")
    expect(display.transitions == expected_rooms, f"{display.transitions} transitions shown")

    # Manipulation checks after every block.
    checks = read_rows(data_dir / "P001_checks.csv")
    by_block: dict[str, dict[str, list[dict]]] = {}
    for row in checks:
        by_block.setdefault(row["block"], {}).setdefault(row["measure"], []).append(row)
    expect(sorted(by_block) == [str(b) for b in range(1, blocks + 1)], f"checks saved for blocks {sorted(by_block)}")
    for block, measures in by_block.items():
        trials = measures.get("digit_span_trial", [])
        right = 2 * (SPAN_RIGHT_UP_TO - config.span_start + 1)
        expect(len(trials) == right + 2, f"block {block}: {len(trials)} digit-span trials")
        expect(measures.get("digit_span_longest", [{}])[0].get("value") == str(SPAN_RIGHT_UP_TO),
               f"block {block}: wrong longest span")
        expect(measures.get("digit_span_total_correct", [{}])[0].get("value") == str(right),
               f"block {block}: wrong span total")
        for question_id, *_ in config.slider_questions:
            answer = measures.get(question_id, [{}])[0]
            expect(answer.get("value") == str(SLIDER_ANSWER), f"block {block}: {question_id} not saved")
            expect(answer.get("rt_ms", "") != "" and answer.get("first_click_ms", "") != "",
                   f"block {block}: {question_id} times not saved")
        expect(len({r["condition"] for rs in measures.values() for r in rs}) == 1, "checks mix conditions")

    # Nothing shown on any screen may reveal a condition, and nothing waits for the experimenter.
    shown = display.shown
    leaks = [t for t in shown if t in set(config.conditions) or "condition" in t.lower()]
    expect(not leaks, f"condition shown on screen: {leaks}")
    expect(PAUSE_TEXT not in shown, "experimenter pause is still shown")
    expect(shown.count("Practice room") == blocks, f"practice room shown {shown.count('Practice room')} times")
    expect(shown.count("Remember where objects belong.") == blocks + expected_rooms,
           "'Remember where objects belong.' missing from an instruction screen")
    header = set(rows[0]) | set(checks[0])
    expect(not {"name", "email", "birthdate", "age"} & header, "personal detail column in results")

    # Crash after the first room, then resume.
    play(config, assets, data_dir, 2, crash_after_room=True)
    first = read_rows(data_dir / "P002_results.csv")
    expect(len(first) == n, f"crash should leave {n} saved rows, got {len(first)}")
    expect(not Session(config, data_dir, 2).is_complete(), "crashed session reported as complete")
    display = play(config, assets, data_dir, 2)
    final = read_rows(data_dir / "P002_results.csv")
    expect(len(final) == n * expected_rooms, f"resume left {len(final)} rows")
    expect(len({(r["block"], r["room"], r["object"]) for r in final}) == len(final), "resume duplicated rows")
    expect(any(r["session_resumed"] == "1" for r in final), "resumed rows are not marked")
    expect(Session(config, data_dir, 2).is_complete(), "resumed session not marked complete")
    expect(display.shown.count("Practice room") == blocks - 1, "resume repeated block 1's practice")
    expect(len({r["block"] for r in read_rows(data_dir / "P002_checks.csv")}) == blocks, "resume lost checks")
    before = (data_dir / "P002_results.csv").read_bytes()
    Session(config, data_dir, 2)
    expect((data_dir / "P002_results.csv").read_bytes() == before, "reopening changed finished data")

    # The no-study baseline group: separate files, no study, no checks, no condition.
    display = play(config, assets, data_dir, 3, baseline=True)
    base = read_rows(data_dir / "B003_results.csv")
    expect(len(base) == n * expected_rooms, f"baseline wrote {len(base)} rows")
    expect({r["condition"] for r in base} == {"baseline"}, "baseline rows carry a condition")
    expect({r["study_ms"] for r in base} == {"0"}, "baseline participants saw the study room")
    expect(not (data_dir / "B003_checks.csv").exists(), "baseline did manipulation checks")
    expect(display.shown.count("Practice room") == 1, "baseline should practise once")
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
