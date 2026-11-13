"""Build a small synthetic assets folder: plain rooms with spots, and coloured
blobs in place of the photos and made objects. Lets the full session run in tests
and on GitHub, where the dataset photos are not available."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).parents[1]
# (surface, max width m, max height m, count)
SPOT_KINDS = [("floor", 0.75, 1.3, 4), ("table", 0.6, 0.55, 4), ("shelf", 0.6, 0.45, 4),
              ("wall", 0.8, 1.2, 2), ("lean", 0.6, 1.3, 2)]
# Spots far enough apart that the largest objects never cover each other, and a
# scale at which the smallest photo is still drawn at MIN_PX.
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
                          "y": 1000 + (k // 8) * 950, "px_per_m": PX_PER_M, "max_w_m": w, "max_h_m": h,
                          "squash": 0.3, "light": [0.9, 0.88, 0.85]})
            k += 1
    (out / "room.json").write_text(json.dumps({"width": WIDTH, "height": HEIGHT, "image": "base.jpg",
                                               "spots": spots}), encoding="utf-8")


def make(folder: Path, decoys: int = 180, practice_decoys: int = 20) -> Path:
    folder = Path(folder)
    for name in ("storage", "laundry", "workshop", "practice"):
        room(folder, name)
    rows = []
    with open(ROOT / "art" / "dataset_photos.csv", encoding="utf-8", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle)):
            # A blob with roughly the photo's shape: tall things tall, wide things wide.
            tall = row["surfaces"] in ("lean", "wall", "floor") or row["name"] in ("tabascosauce", "bottleofwhitewine")
            blob(folder / "objects" / "photos" / f"{row['name']}.png", (60, 120) if tall else (120, 80),
                 (40 + i * 5, 90, 160))
            rows.append({**row, "pool": "target"})
    for i in range(decoys):
        blob(folder / "objects" / "made" / f"decoy_{i:03d}.png", (100, 100), (160, 60 + i % 150, 70))
        rows.append({"name": f"decoy_{i:03d}", "label": f"decoy {i}", "category": "thing", "width_m": 0.2,
                     "surfaces": "table|shelf", "rotate_deg": 0, "pool": "decoy"})
    for i in range(4):
        blob(folder / "objects" / "made" / f"practice_{i}.png", (100, 100), (60, 160, 60))
        rows.append({"name": f"practice_{i}", "label": f"practice {i}", "category": "thing", "width_m": 0.2,
                     "surfaces": "table|shelf", "rotate_deg": 0, "pool": "practice_target"})
    for i in range(practice_decoys):
        blob(folder / "objects" / "made" / f"practice_decoy_{i:02d}.png", (100, 100), (60, 60, 160))
        rows.append({"name": f"practice_decoy_{i:02d}", "label": f"practice decoy {i}", "category": "thing",
                     "width_m": 0.2, "surfaces": "table|shelf", "rotate_deg": 0, "pool": "practice_decoy"})
    with open(folder / "objects" / "objects.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "label", "category", "width_m", "surfaces",
                                                    "rotate_deg", "pool"])
        writer.writeheader()
        writer.writerows(rows)
    return folder
