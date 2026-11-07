"""Screen layout and drag-and-drop logic, with no graphics library.

Everything here works in canvas coordinates: a fixed 1920x1080 canvas, origin at
the top left, y pointing down. The display layer scales the canvas to the real
screen. Keeping this logic graphics-free lets the self-test play a whole session
without a window, on any computer.

  room     1600x900 at (160, 0), identical in the study and placement phases
  tray     the strip under the room, with one slot per object
  Done     the button at the right end of the tray
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .session import PlacementRound, RoomObject

CANVAS = (1920, 1080)
ROOM_ORIGIN = (160, 0)
ROOM_SIZE = (1600, 900)
TRAY_TOP = 900
TRAY_HEIGHT = 180
DONE_RECT = (1730, 925, 170, 130)  # x, y, width, height
SLOT_AREA_WIDTH = 1710
# Every object is shown at the same size, in the tray and in the room, so its
# on-screen size never hints at how far away it was.
ICON_PX = 100


def inside(rect: tuple[float, float, float, float], point: tuple[float, float]) -> bool:
    x, y, w, h = rect
    return x <= point[0] < x + w and y <= point[1] < y + h


def in_room(point: tuple[float, float]) -> bool:
    return inside((*ROOM_ORIGIN, *ROOM_SIZE), point)


def to_room(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] - ROOM_ORIGIN[0], point[1] - ROOM_ORIGIN[1]


def to_canvas(point: tuple[float, float]) -> tuple[float, float]:
    return point[0] + ROOM_ORIGIN[0], point[1] + ROOM_ORIGIN[1]


@dataclass
class Icon:
    """The neutral picture of one object: drawn size, and which pixels are solid."""
    path: Path
    size: tuple[int, int]
    solid: list[list[bool]]  # solid[row][col], at drawn size
    image: object = None  # the trimmed RGBA picture (a PIL image), for the display to draw

    def hit(self, local: tuple[float, float]) -> bool:
        col, row = int(local[0]), int(local[1])
        return 0 <= row < len(self.solid) and 0 <= col < len(self.solid[row]) and self.solid[row][col]


def load_icon(path: Path, box: int = ICON_PX) -> Icon:
    """Read an icon file and work out its drawn size, so that its longest side is `box`."""
    from PIL import Image

    with Image.open(path) as image:
        image = image.convert("RGBA")
        bbox = image.getchannel("A").point(lambda a: 255 if a > 30 else 0).getbbox()
        if bbox is None:
            raise ValueError(f"{path} is empty")
        image = image.crop(bbox)
        scale = box / max(image.size)
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        alpha = image.getchannel("A").resize(size)
        pixels = alpha.load()
        solid = [[pixels[c, r] > 30 for c in range(size[0])] for r in range(size[1])]
        image.load()
    return Icon(path, size, solid, image)


def tray_slots(order: list[RoomObject]) -> dict[str, tuple[float, float]]:
    """Centre of each object's tray slot, spaced evenly along the tray."""
    slot_w = SLOT_AREA_WIDTH / max(len(order), 1)
    centre_y = TRAY_TOP + TRAY_HEIGHT / 2
    return {obj.id: (10 + slot_w * (i + 0.5), centre_y) for i, obj in enumerate(order)}


@dataclass
class PlacementController:
    """Turns pointer presses, moves and releases into placements.

    The display feeds it events and draws its state; it never draws anything.
    """
    round: PlacementRound
    order: list[RoomObject]
    icons: dict[str, Icon]
    slots: dict[str, tuple[float, float]] = field(init=False)
    stacking: list[str] = field(default_factory=list)  # placed objects, last drawn on top
    dragging: str | None = None
    pointer: tuple[float, float] = (0.0, 0.0)
    grab: tuple[float, float] = (0.0, 0.0)
    finished_ms: int | None = None

    def __post_init__(self) -> None:
        self.slots = tray_slots(self.order)

    # ------------------------------------------------------------ queries
    def placed_centre(self, object_id: str) -> tuple[float, float]:
        return to_canvas(self.round.placements[object_id].position)

    def in_tray(self, object_id: str) -> bool:
        return self.round.placements[object_id].position is None and object_id != self.dragging

    def dragged_centre(self) -> tuple[float, float]:
        return self.pointer[0] - self.grab[0], self.pointer[1] - self.grab[1]

    def _hits(self, object_id: str, centre: tuple[float, float], point: tuple[float, float]) -> bool:
        icon = self.icons[object_id]
        local = (point[0] - centre[0] + icon.size[0] / 2, point[1] - centre[1] + icon.size[1] / 2)
        return icon.hit(local)

    def _tray_hit(self, point) -> str | None:
        for obj in self.order:
            icon = self.icons[obj.id]
            sx, sy = self.slots[obj.id]
            box = (sx - icon.size[0] / 2, sy - icon.size[1] / 2, *icon.size)
            if self.round.placements[obj.id].position is None and inside(box, point):
                return obj.id  # the whole slot box counts, so small objects are easy to pick up
        return None

    def _placed_hit(self, point) -> str | None:
        for object_id in reversed(self.stacking):
            if self._hits(object_id, self.placed_centre(object_id), point):
                return object_id
        return None

    # ------------------------------------------------------------ events
    def move(self, point: tuple[float, float]) -> None:
        self.pointer = point

    def press(self, point: tuple[float, float], now_ms: int) -> bool:
        """Handle a left-button press. Returns True when Done was pressed and accepted."""
        self.pointer = point
        if self.dragging:
            return False
        if inside(DONE_RECT, point):
            if self.round.can_finish:
                self.finished_ms = now_ms - self.round.started_ms
                return True
            return False
        picked = self._placed_hit(point)
        if picked:
            cx, cy = self.placed_centre(picked)
            self.grab = (point[0] - cx, point[1] - cy)
            self.stacking.remove(picked)
            self.dragging = picked
            return False
        picked = self._tray_hit(point)
        if picked:
            self.grab = (0.0, 0.0)
            self.dragging = picked
        return False

    def release(self, point: tuple[float, float], now_ms: int) -> None:
        self.pointer = point
        if not self.dragging:
            return
        centre = self.dragged_centre()
        if in_room(centre):
            self.round.drop(self.dragging, to_room(centre), now_ms)
            self.stacking.append(self.dragging)
        else:
            self.round.drop(self.dragging, None, now_ms)  # back to the tray
        self.dragging = None
