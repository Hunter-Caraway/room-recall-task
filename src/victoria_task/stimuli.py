"""The objects and rooms the task draws on, read from assets/.

Every picture is a flat drawing (made by art/build_drawn.py). assets/objects/objects.csv
lists every object drawing, one row each:

  name        file stem; the picture is objects/drawings/<name>.png (RGBA, transparent background)
  label       plain name, for the data file
  category    loose kind (ball, cup, hand tool), so decoys sharing a target's kind can be analysed
  size_m      real length of the object's longest side, in metres
  surfaces    where it can be: any of floor, table, shelf, wall (on a hook), lean (against a
              wall); "grid" for decoys, which are only ever shown in the grid
  pool        target (drawn BOSS object), decoy (grid only), practice_target, practice_decoy

assets/rooms/<room>/room.json describes a drawn room and its spots: where an object may
stand, on which surface, how many pixels a metre is there and the largest object it takes.
A wall spot is a hook: objects hang from it. "blocked" lists the screen boxes of the
filler already drawn in the picture; no target may cover them.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

MIN_PX = 30  # an object must be drawn at least this big (longest side) to be seen in 30 s
PICTURES = "drawings"

Box = tuple[float, float, float, float]
OVERLAP_PX = 4  # boxes may touch or graze by this much


@dataclass(frozen=True)
class Item:
    name: str
    label: str
    category: str
    size_m: float
    surfaces: tuple[str, ...]
    pool: str
    path: Path
    pixel_size: tuple[int, int]  # the drawing's width and height in pixels


@dataclass(frozen=True)
class Spot:
    id: str
    surface: str
    x: float  # room pixels: bottom centre of the object (top centre under the hook, for wall spots)
    y: float
    px_per_m: float
    max_w_m: float
    max_h_m: float

    def size(self, item: Item) -> tuple[float, float]:
        """Width and height in metres."""
        scale = item.size_m / max(item.pixel_size)
        return item.pixel_size[0] * scale, item.pixel_size[1] * scale

    def fits(self, item: Item) -> bool:
        if self.surface not in item.surfaces:
            return False
        w, h = self.size(item)
        return w <= self.max_w_m and h <= self.max_h_m and max(w, h) * self.px_per_m >= MIN_PX

    def box(self, item: Item) -> Box:
        """Screen box the item covers here: bottom centre on the spot, or hanging from it."""
        w, h = (v * self.px_per_m for v in self.size(item))
        top = self.y if self.surface == "wall" else self.y - h
        return (self.x - w / 2, top, self.x + w / 2, top + h)


def overlap(a: Box, b: Box) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > OVERLAP_PX and min(a[3], b[3]) - max(a[1], b[1]) > OVERLAP_PX


@dataclass(frozen=True)
class Room:
    name: str
    width: int
    height: int
    image: Path
    spots: tuple[Spot, ...]
    blocked: tuple[Box, ...] = ()  # screen boxes of the filler already in the picture


def load_items(assets: Path) -> dict[str, Item]:
    from PIL import Image

    folder = Path(assets) / "objects"
    items = {}
    with open(folder / "objects.csv", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            path = folder / PICTURES / f"{row['name']}.png"
            if not path.exists():
                raise FileNotFoundError(f"missing object picture {path}")
            with Image.open(path) as image:
                size = image.size
            items[row["name"]] = Item(
                name=row["name"], label=row["label"], category=row["category"], size_m=float(row["size_m"]),
                surfaces=tuple(row["surfaces"].split("|")), pool=row["pool"], path=path, pixel_size=size,
            )
    return items


def pool(items: dict[str, Item], name: str) -> list[Item]:
    """Items of one pool, in a fixed order (by name), so shuffles repeat exactly."""
    return sorted((i for i in items.values() if i.pool == name), key=lambda i: i.name)


def load_room(assets: Path, name: str) -> Room:
    folder = Path(assets) / "rooms" / name
    raw = json.loads((folder / "room.json").read_text(encoding="utf-8"))
    spots = tuple(
        Spot(s["id"], s["surface"], float(s["x"]), float(s["y"]), float(s["px_per_m"]),
             float(s["max_w_m"]), float(s["max_h_m"]))
        for s in raw["spots"]
    )
    blocked = tuple(tuple(float(v) for v in b) for b in raw.get("blocked", ()))
    return Room(name, int(raw["width"]), int(raw["height"]), folder / raw["image"], spots, blocked)
