"""Turn the cutouts and renders into the game's assets/ folder.

  python art/assemble_assets.py

Reads:
  art/dataset_photos.csv + art/dataset_cutouts/   target photos (cutout_photos.py)
  art/made_objects.csv + _downloads/raw/objects/  studio shots (render_objects.py)
  _downloads/raw/basements/<room>/                empty room + spots.json (build_basements.py)
Writes:
  assets/objects/objects.csv, photos/, made/
  assets/rooms/<room>/base.jpg (empty room with the filler added) and room.json (target spots)

Fails if a target spot stands on the filler. The deal itself keeps targets
off the filler and off each other, using the filler boxes saved in room.json.
"""
import csv
import json
import math
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "art"
RAW = ART / "_downloads" / "raw"
OUT = ROOT / "assets"
sys.path.insert(0, str(ROOT / "src"))

from victoria_task.composite import anchor, compose, prepared  # noqa: E402
from victoria_task.stimuli import Item, Spot  # noqa: E402

MAX_SIDE = 512  # px; larger than any object is ever drawn (about 420 px at most)
ROOMS = ["storage", "laundry", "workshop", "practice"]
PRACTICE_TARGETS = 4
FIELDS = ["name", "label", "category", "width_m", "surfaces", "rotate_deg", "pool"]


def save_cutout(image, target):
    box = image.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    image = image.crop(box)
    full_width = image.width
    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    return full_width


def objects():
    rows, made = [], {}
    with open(ART / "dataset_photos.csv", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            source = ART / "dataset_cutouts" / f"{row['name']}.png"
            save_cutout(Image.open(source).convert("RGBA"), OUT / "objects" / "photos" / f"{row['name']}.png")
            rows.append({k: row[k] for k in FIELDS if k in row} | {"pool": "target"})
    dims = json.loads((ART / "model_dims.json").read_text())
    with open(ART / "made_objects.csv", encoding="utf-8", newline="") as handle:
        made_rows = list(csv.DictReader(handle))
    missing = [r["name"] for r in made_rows if not (RAW / "objects" / f"{r['name']}.png").exists()]
    if missing:
        raise SystemExit(f"{len(missing)} studio shots missing, e.g. {missing[:5]}: run render_objects.py")
    for row in made_rows:
        image = Image.open(RAW / "objects" / f"{row['name']}.png").convert("RGBA")
        m_per_px = json.loads((RAW / "objects" / f"{row['name']}.json").read_text())["m_per_px"]
        pool_dir = "made"
        saved = OUT / "objects" / pool_dir / f"{row['name']}.png"
        width_px = save_cutout(image, saved)
        width = width_px * m_per_px
        listed = max(dims.get(row["model"], [width]))
        if listed and abs(math.log10(width / listed)) > 0.7:  # model file in the wrong unit (10x or 100x off)
            width /= 10 ** round(math.log10(width / listed))
        made[row["name"]] = row | {"width_m": f"{width:.3f}", "height_m": width * Image.open(saved).height / Image.open(saved).width}
    # Practice targets: the first few practice objects small enough for a table or shelf.
    practice = [r for r in made.values() if r["pool"] == "practice"]
    small = [r for r in practice if 0.1 <= float(r["width_m"]) <= 0.4 and r["height_m"] <= 0.35][:PRACTICE_TARGETS]
    for row in made.values():
        if row["pool"] == "filler":
            continue
        pool = row["pool"]
        surfaces = row["surfaces"]
        if pool == "practice":
            pool = "practice_target" if row in small else "practice_decoy"
            surfaces = surfaces or ("table|shelf" if row in small else "")
        rows.append({"name": row["name"], "label": row["label"], "category": row["category"],
                     "width_m": row["width_m"], "surfaces": surfaces or "-", "rotate_deg": row["rotate_deg"] or 0,
                     "pool": pool})
    with open(OUT / "objects" / "objects.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"objects: {sum(r['pool'] == 'target' for r in rows)} targets, "
          f"{sum(r['pool'] == 'decoy' for r in rows)} decoys, "
          f"{sum(r['pool'].startswith('practice') for r in rows)} practice")
    return made


def to_spot(record):
    return Spot(record["id"], record["surface"], record["x"], record["y"], record["px_per_m"],
                record["max_w_m"], record["max_h_m"], record["squash"], tuple(record["light"]))


def room(name, made):
    raw = RAW / "basements" / name
    data = json.loads((raw / "spots.json").read_text())
    targets = [r for r in data["spots"] if "filler" not in r]
    fillers = [r for r in data["spots"] if "filler" in r]
    placed = []
    for record in fillers:
        row = made[record["filler"]]
        item = Item(row["name"], row["label"], row["category"], float(row["width_m"]), (record["surface"],), 0.0,
                    "filler", OUT / "objects" / "made" / f"{row['name']}.png", (1, 1))
        placed.append((item, to_spot(record)))
    out = OUT / "rooms" / name
    out.mkdir(parents=True, exist_ok=True)
    picture = compose(Image.open(raw / "empty.png"), placed)
    picture.save(out / "base.jpg", quality=92, subsampling=0)
    blocked = []
    for item, spot in placed:
        image = prepared(item, spot)
        x, y = anchor(image, spot)
        blocked.append((item.name, (x, y, x + image.width, y + image.height)))
    (out / "room.json").write_text(json.dumps({"width": data["width"], "height": data["height"],
                                               "image": "base.jpg", "spots": targets,
                                               "blocked": [list(b) for _, b in blocked]}, indent=1))
    # The deal keeps targets off the filler and off each other; here only check that
    # every spot's standing point is clear of the filler, or the spot could never be used.
    problems = []
    for record in targets:
        x, y = record["x"], record["y"]
        for name_, (x0, y0, x1, y1) in blocked:
            if x0 + 4 < x < x1 - 4 and y0 + 4 < y < y1 - 4:
                problems.append(f"{name}: spot {record['id']} stands on filler {name_}")
    print(f"{name}: {len(targets)} target spots, {len(fillers)} filler")
    return problems


def main():
    made = objects()
    problems = []
    for name in ROOMS:
        if (RAW / "basements" / name / "spots.json").exists():
            problems += room(name, made)
        else:
            problems.append(f"{name}: not rendered yet")
    for problem in problems:
        print("PROBLEM", problem)
    print("assemble:", "FAILED" if problems else "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
