"""Build every picture the task uses from the drawings in art/drawings/.

  assets/objects/drawings/<name>.png   each object, longest side 512 px, transparent background
  assets/objects/objects.csv           one row per object (see src/victoria_task/stimuli.py)
  assets/rooms/<room>/base.png         the room with its filler drawn in
  assets/rooms/<room>/room.json        its spots and the screen boxes of the filler

Needs cairosvg (build time only):  .venv/bin/python art/build_drawn.py
Then it checks that every participant number up to 120 gets a deal that fits.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import sys
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from art.drawings import decoys, filler, practice, practice_decoys, rooms, targets, targets2  # noqa: E402,F401
from victoria_task.composite import compose  # noqa: E402
from victoria_task.stimuli import Item, Spot  # noqa: E402

ASSETS = ROOT / "assets"
LONGEST = 512
FIELDS = ["name", "label", "category", "size_m", "surfaces", "pool"]


def render(svg_text: str, longest: int | None = None) -> Image.Image:
    probe = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg_text.encode()))).size
    scale = (longest / max(probe)) if longest else 1.0
    png = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=round(probe[0] * scale),
                           output_height=round(probe[1] * scale))
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    box = image.getchannel("A").getbbox()
    return image.crop(box) if box else image


def build_objects() -> list[dict]:
    folder = ASSETS / "objects" / "drawings"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    draw = {**targets.DRAW, **practice.DRAW, **decoys.DRAW, **practice_decoys.DRAW}
    with open(ROOT / "art" / "drawings" / "objects.csv", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for pool_name, table in (("decoy", decoys.DECOYS), ("practice_decoy", practice_decoys.DECOYS)):
        for name, (label, category, size_m) in table.items():
            rows.append({"name": name, "label": label, "category": category, "size_m": f"{size_m:g}",
                         "surfaces": "grid", "pool": pool_name})
    names = [r["name"] for r in rows]
    if len(set(names)) != len(names):
        raise SystemExit("an object name is used twice")
    missing = [n for n in names if n not in draw]
    if missing:
        raise SystemExit(f"no drawing for {missing}")
    for name in names:
        render(draw[name](), LONGEST).save(folder / f"{name}.png", optimize=True)
    with open(ASSETS / "objects" / "objects.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} objects drawn")
    return rows


def build_room(name: str) -> None:
    picture_svg, spots, fill = rooms.ROOMS[name]()
    folder = ASSETS / "rooms" / name
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("base.*"):
        old.unlink()
    base = render(picture_svg).convert("RGB")
    placements, blocked = [], []
    tmp = ROOT / "art" / "_preview" / "filler"
    tmp.mkdir(parents=True, exist_ok=True)
    for kind, x, y, px in fill:
        path = tmp / f"{kind}.png"
        image = render(filler.DRAW[kind](), LONGEST)
        image.save(path)
        item = Item(kind, kind, "filler", filler.FILLER_SIZE[kind], ("filler",), "filler", path, image.size)
        spot = Spot(kind, "floor", x, y, px, 99, 99)
        placements.append((item, spot))
        blocked.append([round(v, 1) for v in spot.box(item)])
    compose(base, placements).save(folder / "base.png", optimize=True)
    (folder / "room.json").write_text(json.dumps({
        "width": base.width, "height": base.height, "image": "base.png", "spots": spots, "blocked": blocked,
    }, indent=1), encoding="utf-8")
    print(f"room {name}: {len(spots)} spots, {len(blocked)} filler")


def check_deals(participants: int = 120) -> None:
    from victoria_task.config import load_config
    from victoria_task.deal import deal, practice_trial
    from victoria_task.schedule import build_schedule
    from victoria_task.stimuli import load_items, load_room, pool

    config = load_config(ROOT / "config.toml")
    items = load_items(ASSETS)
    room_map = {n: load_room(ASSETS, n) for n in dict.fromkeys([config.practice_room, *config.rooms])}
    for target in pool(items, "target"):
        if not any(s.fits(target) for r in config.rooms for s in room_map[r].spots):
            raise SystemExit(f"{target.name} fits no spot in any room")
    for p in range(1, participants + 1):
        blocks = build_schedule(p, config.conditions, config.rooms)
        deal(p, blocks, room_map, pool(items, "target"), pool(items, "decoy"), config.tiles)
        practice_trial(p, room_map[config.practice_room], pool(items, "practice_target"),
                       pool(items, "practice_decoy"), config.tiles)
    print(f"deals fit for participants 1-{participants}")


if __name__ == "__main__":
    build_objects()
    for room_name in rooms.ROOMS:
        build_room(room_name)
    check_deals()
