"""Build a small synthetic assets folder: plain rooms with spots, and coloured
blobs in place of the drawings. Lets the full session run in tests quickly and
without depending on the real rooms' layout."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).parents[1]
# (surface, max width m, max height m, count)
SPOT_KINDS = [("floor", 1.0, 1.3, 4), ("table", 0.6, 0.55, 4), ("shelf", 0.6, 0.45, 4), ("wall", 0.8, 1.2, 2),
              ("lean", 0.6, 1.3, 2)]
# Spots far enough apart that the largest objects never cover each other, and a
# scale at which the smallest object is still drawn at MIN_PX.
PX_PER_M = 700
WIDTH, HEIGHT = 4400, 2000


def blob(path: Path, size: tuple[int, int], colour: tuple[int, int, int]) -> None:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((0, 0, size[0] - 1, size[1] - 1), fill=(*colour, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def room(folder: Path, name: str) -> None:
    out = folder / "rooms" / name
    out.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (WIDTH, HEIGHT), (120, 115, 108)).save(out / "base.jpg")
    spots, k = [], 0
    for surface, w, h, count in SPOT_KINDS:
        for _ in range(count):
            spots.append({"id": f"{surface}_{k}", "surface": surface, "x": 300 + (k % 8) * 530,
                          "y": 1000 + (k // 8) * 950, "px_per_m": PX_PER_M, "max_w_m": w, "max_h_m": h})
            k += 1
    (out / "room.json").write_text(json.dumps({"width": WIDTH, "height": HEIGHT, "image": "base.jpg",
                                               "spots": spots}), encoding="utf-8")


def make(folder: Path, decoys: int = 180, practice_decoys: int = 20) -> Path:
    folder = Path(folder)
    for name in ("storage", "laundry", "workshop", "practice"):
        room(folder, name)
    rows = []
    pictures = folder / "objects" / "drawings"
    with open(ROOT / "art" / "drawings" / "objects.csv", encoding="utf-8", newline="") as handle:
        for i, row in enumerate(r for r in csv.DictReader(handle) if r["pool"] == "target"):
            # A blob with roughly the drawing's shape: hanging and leaning things tall, others wide.
            tall = bool({"wall", "lean"} & set(row["surfaces"].split("|")))
            blob(pictures / f"{row['name']}.png", (60, 120) if tall else (120, 80), (40 + i * 5, 90, 160))
            rows.append(row)
    for prefix, pool_name, count, surfaces, colour in (("decoy", "decoy", decoys, "grid", (160, 60, 70)),
                                                       ("practice", "practice_target", 4, "table|shelf", (60, 160, 60)),
                                                       ("practice_decoy", "practice_decoy", practice_decoys, "grid",
                                                        (60, 60, 160))):
        for i in range(count):
            name = f"{prefix}_{i:03d}"
            blob(pictures / f"{name}.png", (100, 100), colour)
            rows.append({"name": name, "label": name.replace("_", " "), "category": "thing", "size_m": 0.2,
                         "surfaces": surfaces, "pool": pool_name})
    with open(folder / "objects" / "objects.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "label", "category", "size_m", "surfaces", "pool"])
        writer.writeheader()
        writer.writerows(rows)
    return folder
