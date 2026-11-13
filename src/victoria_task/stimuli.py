"""The objects and rooms the task draws on, read from assets/.

assets/objects/objects.csv lists every object picture, one row each:

  name        file stem; the picture is objects/<pool folder>/<name>.png (RGBA cutout)
  label       plain name, for the data file
  category    loose kind (ball, cup, hand tool), so decoys sharing a target's kind can be analysed
  width_m     real width of the object as photographed, in metres
  surfaces    where it can sit: any of floor, table, shelf, wall, lean (against a wall), joined by |
  rotate_deg  turn in the picture plane before placing, counter-clockwise, so it rests naturally
  pool        target (dataset photo), decoy (made, grid only), practice_target, practice_decoy

assets/rooms/<room>/room.json describes a rendered room and its spots: where an
object may stand, on which surface, how many pixels a metre is there, the largest
object it takes and the light falling on it. "blocked" lists the screen boxes of the
filler already in the picture; no target may cover them.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

MIN_PX = 34  # an object must be drawn at least this big (longest side) to be seen in 30 s
POOL_FOLDERS = {"target": "photos", "decoy": "made", "practice_target": "made", "practice_decoy": "made"}


@dataclass(frozen=True)
class Item:
    name: str
    label: str
    category: str
    width_m: float
    surfaces: tuple[str, ...]
    rotate_deg: float
    pool: str
    path: Path
    pixel_size: tuple[int, int]  # the cutout's width and height in pixels

    def real_size(self) -> tuple[float, float]:
        """Width and height in metres after the turn, as placed in a room."""
        w = self.width_m
        h = w * self.pixel_size[1] / self.pixel_size[0]
        a = math.radians(self.rotate_deg)
        return (abs(w * math.cos(a)) + abs(h * math.sin(a)), abs(w * math.sin(a)) + abs(h * math.cos(a)))


@dataclass(frozen=True)
class Spot:
    id: str
    surface: str
    x: float  # room pixels: bottom centre of the object (centre for wall spots)
    y: float
    px_per_m: float
    max_w_m: float
    max_h_m: float
    squash: float  # ground-plane ellipse height / width at this spot, for contact shadows
    light: tuple[float, float, float]  # colour multiplier for the light at this spot

    def fits(self, item: Item) -> bool:
        if self.surface not in item.surfaces:
            return False
        w, h = item.real_size()
        return w <= self.max_w_m and h <= self.max_h_m and max(w, h) * self.px_per_m >= MIN_PX

    def box(self, item: Item) -> Box:
        """Screen box the item covers here: bottom centre on the spot, or centred on a wall."""
        w, h = (v * self.px_per_m for v in item.real_size())
        top = self.y - h / 2 if self.surface == "wall" else self.y - h
        return (self.x - w / 2, top, self.x + w / 2, top + h)


Box = tuple[float, float, float, float]
OVERLAP_PX = 4  # boxes may touch or graze by this much


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
            path = folder / POOL_FOLDERS[row["pool"]] / f"{row['name']}.png"
            if not path.exists():
                raise FileNotFoundError(f"missing object picture {path}")
            with Image.open(path) as image:
                size = image.size
            items[row["name"]] = Item(
                name=row["name"], label=row["label"], category=row["category"],
                width_m=float(row["width_m"]), surfaces=tuple(row["surfaces"].split("|")),
                rotate_deg=float(row["rotate_deg"] or 0), pool=row["pool"], path=path, pixel_size=size,
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
             float(s["max_w_m"]), float(s["max_h_m"]), float(s.get("squash", 0.25)),
             tuple(s.get("light", (1.0, 1.0, 1.0))))
        for s in raw["spots"]
    )
    blocked = tuple(tuple(float(v) for v in b) for b in raw.get("blocked", ()))
    return Room(name, int(raw["width"]), int(raw["height"]), folder / raw["image"], spots, blocked)
