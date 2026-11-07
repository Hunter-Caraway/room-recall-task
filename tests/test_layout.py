"""Drag-and-drop logic and scoring helpers, with synthetic icons."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from victoria_task.filler import problems
from victoria_task.layout import DONE_RECT, Icon, PlacementController, to_canvas
from victoria_task.scoring import nearest_other, swap
from victoria_task.session import PlacementRound, RoomInfo, RoomObject

DONE = (DONE_RECT[0] + 5, DONE_RECT[1] + 5)


def ring(size=20):
    """An icon whose centre is see-through, to check clicks use solid pixels."""
    solid = [[not (5 <= r < 15 and 5 <= c < 15) for c in range(size)] for r in range(size)]
    return Icon(Path("x.png"), (size, size), solid)


def make(n=3):
    objects = [RoomObject(f"o{i}", f"thing {i}", "", (200.0 + 300 * i, 400.0), (10, 10), "icons/x.png")
               for i in range(n)]
    room = RoomInfo("r", 1600, 900, tuple(objects))
    round_ = PlacementRound(room, objects, 0)
    return PlacementController(round_, objects, {o.id: ring() for o in objects}), objects


def test_drag_from_tray_places_object_and_unlocks_done():
    controller, objects = make()
    assert not controller.press(DONE, 10)
    for obj in objects:
        controller.press(controller.slots[obj.id], 20)
        controller.release(to_canvas(obj.center), 30)
    assert controller.round.can_finish
    assert controller.press(DONE, 100)
    assert controller.finished_ms == 100


def test_drop_outside_room_returns_to_tray():
    controller, objects = make()
    controller.press(controller.slots["o0"], 1)
    controller.release((5, 1000), 2)
    assert controller.round.placements["o0"].position is None
    assert controller.in_tray("o0")
    assert controller.round.placements["o0"].moves == 1


def test_click_on_see_through_centre_does_not_pick_up():
    controller, objects = make()
    controller.press(controller.slots["o0"], 1)
    controller.release(to_canvas(objects[0].center), 2)
    centre = controller.placed_centre("o0")
    controller.press(centre, 3)
    assert controller.dragging is None
    controller.press((centre[0] - 8, centre[1]), 4)  # on the ring
    assert controller.dragging == "o0"


def test_swap_scoring():
    targets = {"a": (0, 0), "b": (100, 0)}
    other, distance = nearest_other("a", (98, 0), targets, 1600)
    assert other == "b" and distance < 5
    assert swap(0, distance, 5) == 1
    assert swap(1, distance, 5) == 0


def test_filler_is_repeatable_and_balanced():
    first = problems(4, 1, "kitchen")
    assert first == problems(4, 1, "kitchen")
    share = sum(p.is_true for p in first) / len(first)
    assert 0.35 < share < 0.65
