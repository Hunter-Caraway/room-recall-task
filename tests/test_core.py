import csv
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from victoria_task.data import COLUMNS, ParticipantStore, run_sheet_text
from victoria_task.schedule import balanced_latin_square, build_schedule
from victoria_task.scoring import distance_pct, score


@pytest.mark.parametrize("n", [2, 4, 6])
def test_square_is_latin_and_balanced(n):
    square = balanced_latin_square(n)
    for row in square:
        assert sorted(row) == list(range(n))
    for column in zip(*square):
        assert sorted(column) == list(range(n))
    pairs = Counter((a, b) for row in square for a, b in zip(row, row[1:]))
    assert len(pairs) == n * (n - 1)
    assert set(pairs.values()) == {1}


def test_odd_condition_count_rejected():
    with pytest.raises(ValueError):
        balanced_latin_square(3)


def test_schedule_repeats_for_same_participant():
    conditions = ["A", "B", "C", "D"]
    rooms = [["r1", "r2"], ["r3", "r4"], ["r5", "r6"], ["r7", "r8"]]
    assert build_schedule(7, conditions, rooms) == build_schedule(7, conditions, rooms)


def test_every_condition_meets_every_room_set():
    conditions = ["A", "B", "C", "D"]
    rooms = [["r1"], ["r2"], ["r3"], ["r4"]]
    pairs = Counter()
    for participant in range(1, 17):
        for block in build_schedule(participant, conditions, rooms):
            pairs[(block.condition, block.rooms)] += 1
    assert len(pairs) == 16
    assert set(pairs.values()) == {4}


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
    text = run_sheet_text(35, ["A", "B"], [["kitchen"], ["living_room"]])
    lines = text.strip().splitlines()
    assert len(lines) == 1 + 35 * 2
    assert lines[1].startswith("1,1,A,")
