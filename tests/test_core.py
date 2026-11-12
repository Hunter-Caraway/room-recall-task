import csv
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from victoria_task.checks import (CONTINUE_RECT, SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y, DigitSpan,
                                  SliderController, sequence)
from victoria_task.data import COLUMNS, ParticipantStore, run_sheet_text
from victoria_task.session import PlacementRound, RoomInfo, RoomObject
from victoria_task.schedule import balanced_latin_square, build_schedule
from victoria_task.scoring import distance_pct, score


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_square_is_latin_and_balanced(n):
    square = balanced_latin_square(n)
    rows = n if n % 2 == 0 else 2 * n
    assert len(square) == rows
    for row in square:
        assert sorted(row) == list(range(n))
    for column in zip(*square):
        assert Counter(column) == {c: rows // n for c in range(n)}
    pairs = Counter((a, b) for row in square for a, b in zip(row, row[1:]))
    assert len(pairs) == n * (n - 1)
    assert len(set(pairs.values())) == 1


def test_three_conditions_balance_over_120_participants():
    conditions = ["A", "B", "C"]
    rooms = [["b1", "l1", "g1"], ["b2", "l2", "g2"], ["b3", "l3", "g3"]]
    orders = Counter()
    pairs = Counter()
    first_room = Counter()
    for participant in range(1, 121):
        blocks = build_schedule(participant, conditions, rooms)
        orders[tuple(b.condition for b in blocks)] += 1
        for block in blocks:
            pairs[(block.condition, frozenset(block.rooms))] += 1
            first_room[block.rooms[0][0]] += 1
    assert len(orders) == 6 and set(orders.values()) == {20}
    assert len(pairs) == 9  # every condition meets every arrangement
    assert max(first_room.values()) - min(first_room.values()) < 40  # room type order is mixed
    # Each participant sees each arrangement once, so each room type once per block.
    for participant in range(1, 19):
        blocks = build_schedule(participant, conditions, rooms)
        assert sorted(r for b in blocks for r in b.rooms) == sorted(r for s in rooms for r in s)


def test_schedule_repeats_for_same_participant():
    conditions = ["A", "B", "C", "D"]
    rooms = [["r1", "r2"], ["r3", "r4"], ["r5", "r6"], ["r7", "r8"]]
    assert build_schedule(7, conditions, rooms) == build_schedule(7, conditions, rooms)


@pytest.mark.parametrize("n", [3, 4])
def test_every_condition_meets_every_room_set(n):
    conditions = list("ABCD"[:n])
    rooms = [[f"r{i}"] for i in range(n)]
    cells = len(balanced_latin_square(n)) * n
    pairs = Counter()
    for participant in range(1, cells + 1):
        for block in build_schedule(participant, conditions, rooms):
            pairs[(block.condition, block.rooms)] += 1
    assert len(pairs) == n * n
    assert len(set(pairs.values())) == 1


def test_two_condition_build_has_both_orders_and_rotations():
    seen = {
        tuple((b.condition, b.rooms[0]) for b in build_schedule(p, ["A", "B"], [["k"], ["l"]]))
        for p in range(1, 5)
    }
    assert len(seen) == 4


def test_scoring_boundary_is_inclusive():
    assert distance_pct((0, 0), (80, 0), 1600) == pytest.approx(5.0)
    assert score(5.0, 5.0) == 1
    assert score(5.0001, 5.0) == 0


def row(block, room, obj):
    return {column: "" for column in COLUMNS} | {"block": block, "room": room, "object": obj}


def test_store_round_trip_and_crash_reconcile(tmp_path):
    store = ParticipantStore(tmp_path, 3)
    assert not store.has_session()
    store.save_room([row(1, "kitchen", "jug")], {"finished": [[1, "kitchen"]]})
    store.save_room([row(2, "living", "duck")], {"finished": [[1, "kitchen"], [2, "living"]]})
    store.reconcile({("1", "kitchen")})
    with open(store.csv_path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["object"] for r in rows] == ["jug"]
    assert store.csv_path.name == "P003_results.csv"


def test_run_sheet_lists_every_block():
    text = run_sheet_text(120, ["A", "B", "C"], [["b1", "l1"], ["b2", "l2"], ["b3", "l3"]])
    lines = text.strip().splitlines()
    assert len(lines) == 1 + 120 * 3
    assert lines[1].startswith("1,1,A,")


def test_digit_span_stops_after_two_misses_at_one_length():
    span = DigitSpan(participant=4, block=2, start=2, maximum=8, trials_per_length=2)
    while (step := span.next_digits()) is not None:
        length, trial, digits = step
        assert len(set(digits)) == length
        backward = "".join(map(str, reversed(digits)))
        span.record(length, trial, digits, backward if length < 5 or trial == 2 and length == 5 else "0", 1000)
    # Lengths 2-4 right, one of two right at 5, both wrong at 6.
    assert [t.length for t in span.trials] == [2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    assert span.span == 5
    assert span.total_correct == 7
    assert sequence(4, 2, 3, 1) == sequence(4, 2, 3, 1)


def test_digit_span_stops_at_maximum():
    span = DigitSpan(participant=1, block=1, start=2, maximum=3, trials_per_length=2)
    while (step := span.next_digits()) is not None:
        length, trial, digits = step
        span.record(length, trial, digits, "".join(map(str, reversed(digits))), 1000)
    assert span.span == 3 and len(span.trials) == 4


def test_slider_needs_an_answer_and_clamps():
    slider = SliderController(started_ms=100)
    cont = (CONTINUE_RECT[0] + 5, CONTINUE_RECT[1] + 5)
    assert not slider.press(cont, 200)
    slider.press((SLIDER_LEFT + 2, SLIDER_Y), 300)
    slider.move((SLIDER_RIGHT + 500, SLIDER_Y + 300), 350)
    slider.release((SLIDER_RIGHT + 500, SLIDER_Y + 300), 360)
    assert slider.value == 100 and slider.first_click_ms == 200
    slider.press((SliderController.x_for(25), SLIDER_Y - 20), 400)
    slider.release((SliderController.x_for(25), SLIDER_Y - 20), 410)
    assert slider.value == 25
    assert slider.press(cont, 900) and slider.finished_ms == 800


def test_placement_timing_splits_first_placement_from_corrections():
    room = RoomInfo("r", 1600, 900, (RoomObject("a", "a", "", (100, 100), (10, 10), ""),))
    round_ = PlacementRound(room, list(room.objects), started_ms=1000)
    round_.pick_up("a", 1500)
    round_.drop("a", (90, 90), 2000)
    round_.pick_up("a", 3000)
    round_.drop("a", (100, 100), 3300)
    item = round_.placements["a"]
    assert item.first_pickup_ms == 500 and item.first_placed_ms == 1000
    assert item.held_ms == 800 and item.correction_ms == 300 and item.moves == 2
