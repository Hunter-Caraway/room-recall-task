import csv
import dataclasses
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import fake_assets
from victoria_task.checks import (CONTINUE_RECT, SLIDER_LEFT, SLIDER_RIGHT, SLIDER_Y, DigitSpan,
                                  SliderController, sequence)
from victoria_task.composite import compose, tile
from victoria_task.data import TILE_COLUMNS, TRIAL_COLUMNS, ParticipantStore, run_sheet_text
from victoria_task.deal import deal, place
from victoria_task.grid import DONE_RECT, GridController
from victoria_task.schedule import balanced_latin_square, build_schedule
from victoria_task.scoring import criterion, dprime
from victoria_task.stimuli import load_items, load_room, pool

ROOMS = ["storage", "laundry", "workshop"]


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


def test_conditions_and_room_orders_balance():
    conditions = ["A", "B", "C"]
    orders, first_room, pairs = Counter(), Counter(), Counter()
    for participant in range(1, 37):
        blocks = build_schedule(participant, conditions, ROOMS)
        orders[tuple(b.condition for b in blocks)] += 1
        assert len({b.rooms for b in blocks}) == 3  # a different room order in every block
        for block in blocks:
            assert sorted(block.rooms) == sorted(ROOMS)
            first_room[block.rooms[0]] += 1
            pairs[(block.condition, block.rooms)] += 1
    assert len(orders) == 6 and set(orders.values()) == {6}
    assert set(first_room.values()) == {36}  # each room opens a block equally often
    assert len(pairs) == 18  # every condition meets every room order


def test_schedule_repeats_for_same_participant():
    assert build_schedule(7, ["A", "B", "C"], ROOMS) == build_schedule(7, ["A", "B", "C"], ROOMS)


def test_dprime_and_criterion():
    assert dprime(5, 5, 0, 19) > 2.5
    assert dprime(0, 5, 19, 19) < -2.5
    assert dprime(2, 4, 10, 20) == pytest.approx(0.0, abs=1e-9)
    assert criterion(5, 5, 19, 19) < 0 < criterion(0, 5, 0, 19)


def test_grid_toggles_and_done_always_works():
    grid = GridController([f"t{i}" for i in range(24)], 6, 4, started_ms=1000)
    done = (DONE_RECT[0] + 5, DONE_RECT[1] + 5)
    assert not grid.press(grid.point_of(3), 1500)
    assert not grid.press(grid.point_of(3), 1700)
    assert not grid.press(grid.point_of(5), 1800)
    assert not grid.press((5, 5), 1900)  # outside every tile
    assert [t.selected for t in grid.tiles][3:6] == [False, False, True]
    assert grid.tiles[3].toggles == 2 and grid.tiles[3].first_selected_ms == 500
    assert grid.tiles[3].last_toggle_ms == 700
    assert grid.press(done, 2500) and grid.finished_ms == 1500
    empty = GridController([f"t{i}" for i in range(24)], 6, 4, started_ms=0)
    assert empty.press(done, 10)  # nothing selected is a valid answer


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    return fake_assets.make(tmp_path_factory.mktemp("assets"))


def test_deal_uses_every_target_once_and_never_repeats_a_decoy(assets):
    items = load_items(assets)
    rooms = {r: load_room(assets, r) for r in ROOMS}
    blocks = build_schedule(5, ["A", "B", "C"], ROOMS)
    trials = deal(5, blocks, rooms, pool(items, "target"), pool(items, "decoy"), 12)
    assert trials == deal(5, blocks, rooms, pool(items, "target"), pool(items, "decoy"), 12)
    targets = [n for t in trials for n, _ in t.targets]
    assert sorted(targets) == sorted(i.name for i in pool(items, "target"))
    assert sorted(len(t.targets) for t in trials) == [4, 4, 4, 5, 5, 5, 5, 5, 5]
    decoys = [n for t in trials for n in t.grid if n not in dict(t.targets)]
    assert len(decoys) == len(set(decoys)) == 9 * 12 - 42
    for trial in trials:
        spots = {s.id: s for s in rooms[trial.room].spots}
        assert len({s for _, s in trial.targets}) == len(trial.targets)
        assert all(spots[s].fits(items[n]) for n, s in trial.targets)
        assert set(dict(trial.targets)) <= set(trial.grid) and len(trial.grid) == 12
    other = deal(6, build_schedule(6, ["A", "B", "C"], ROOMS), rooms, pool(items, "target"),
                 pool(items, "decoy"), 12)
    assert [t.targets for t in other] != [t.targets for t in trials]


def test_place_reports_a_room_that_cannot_hold_the_items(assets):
    items = load_items(assets)
    room = load_room(assets, "storage")
    floor = sum(1 for s in room.spots if s.surface == "floor")
    # One more floor-only object than the room has floor spots.
    many = [dataclasses.replace(i, surfaces=("floor",)) for i in pool(items, "decoy")[: floor + 1]]
    assert place(many, room, random.Random(1)) is None
    assert place(many[:floor], room, random.Random(1)) is not None


def test_compose_and_tile_draw_the_objects(assets):
    items = load_items(assets)
    room = load_room(assets, "storage")
    from PIL import Image
    base = Image.open(room.image).convert("RGB")
    item = pool(items, "target")[0]
    spot = next(s for s in room.spots if s.fits(item))
    picture = compose(base, [(item, spot)])
    assert picture.size == base.size and picture.getpixel((int(spot.x), int(spot.y) - 5)) != base.getpixel(
        (int(spot.x), int(spot.y) - 5))
    square = tile(item, 200)
    assert square.size == (200, 200) and square.getpixel((2, 2)) == (255, 255, 255)


def test_store_round_trip_and_crash_reconcile(tmp_path):
    store = ParticipantStore(tmp_path, 3)
    assert not store.has_session()
    tile_row = lambda b, r: {c: "" for c in TILE_COLUMNS} | {"block": b, "room": r}
    trial_row = lambda b, r: {c: "" for c in TRIAL_COLUMNS} | {"block": b, "room": r}
    store.save_trial([tile_row(1, "storage")] * 2, trial_row(1, "storage"), {"finished": [[1, "storage"]]})
    store.save_trial([tile_row(1, "laundry")] * 2, trial_row(1, "laundry"),
                     {"finished": [[1, "storage"], [1, "laundry"]]})
    store.reconcile({("1", "storage")})
    for path, count in ((store.tiles_path, 2), (store.trials_path, 1)):
        with open(path, newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == count and {r["room"] for r in rows} == {"storage"}
    assert store.trials_path.name == "P003_trials.csv"


def test_run_sheet_lists_every_block():
    text = run_sheet_text(120, ["A", "B", "C"], ROOMS)
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
