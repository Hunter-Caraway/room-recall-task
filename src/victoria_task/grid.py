"""The recognition grid's layout and click logic, with no graphics library.

Canvas coordinates: a fixed 1920x1080 canvas, origin top left, y down; the display
scales it to the screen. The study room is drawn at ROOM_ORIGIN, ROOM_SIZE.
"""
from __future__ import annotations

from dataclasses import dataclass, field

CANVAS = (1920, 1080)
ROOM_ORIGIN = (160, 90)
ROOM_SIZE = (1600, 900)
TILE = 200
GAP = 20
GRID_TOP = 100
PROMPT_Y = 50  # centre of the question above the grid
DONE_RECT = (860, 985, 200, 76)  # x, y, width, height
PROMPT = "Click every object that was in the room, then press Done."


def inside(rect: tuple[float, float, float, float], point: tuple[float, float]) -> bool:
    x, y, w, h = rect
    return x <= point[0] < x + w and y <= point[1] < y + h


def tile_rects(columns: int, rows: int) -> list[tuple[int, int, int, int]]:
    width = columns * TILE + (columns - 1) * GAP
    left = (CANVAS[0] - width) // 2
    return [(left + c * (TILE + GAP), GRID_TOP + r * (TILE + GAP), TILE, TILE)
            for r in range(rows) for c in range(columns)]


@dataclass
class TileState:
    selected: bool = False
    toggles: int = 0
    first_selected_ms: int | None = None
    last_toggle_ms: int | None = None


@dataclass
class GridController:
    """Click a tile to select it, click again to deselect; Done always works.
    Times are ms from the grid appearing."""
    names: list[str]
    columns: int
    rows: int
    started_ms: int
    rects: list[tuple[int, int, int, int]] = field(init=False)
    tiles: list[TileState] = field(init=False)
    finished_ms: int | None = None

    def __post_init__(self) -> None:
        if len(self.names) != self.columns * self.rows:
            raise ValueError("one name per tile")
        self.rects = tile_rects(self.columns, self.rows)
        self.tiles = [TileState() for _ in self.names]

    def press(self, point: tuple[float, float], now_ms: int) -> bool:
        """Handle a left click. Returns True when Done was pressed."""
        elapsed = now_ms - self.started_ms
        if inside(DONE_RECT, point):
            self.finished_ms = elapsed
            return True
        for rect, state in zip(self.rects, self.tiles):
            if inside(rect, point):
                state.selected = not state.selected
                state.toggles += 1
                state.last_toggle_ms = elapsed
                if state.selected and state.first_selected_ms is None:
                    state.first_selected_ms = elapsed
                break
        return False

    def point_of(self, index: int) -> tuple[float, float]:
        x, y, w, h = self.rects[index]
        return x + w / 2, y + h / 2
