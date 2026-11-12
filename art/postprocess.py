"""Turn raw Blender output into game assets, and verify each scored object is usable."""
import json
import pathlib
import sys

from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "art" / "_downloads" / "raw"
OUT = ROOT / "assets"
MIN_VISIBLE = 0.90  # share of each object not blocked by something in front of it
EDGE_MARGIN = 6  # px from the image border
MIN_SIDE = 28  # px; smaller objects are too hard to see
MIN_SPACING = 0.10  # share of room width between correct spots: twice the 5% tolerance
ICON_BOX, ICON_LONG_SIDE = 160, 150  # px
ROOM_TYPES = ("bedroom", "living_room", "garage", "hallway")
ARRANGEMENTS = (1, 2, 3)
ROOMS = tuple(f"{kind}_{k}" for kind in ROOM_TYPES for k in ARRANGEMENTS)


def build_icon(source, target):
    """Trim the studio render, scale its longest side to 150 px, centre it on 160x160."""
    image = Image.open(source).convert("RGBA")
    box = image.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if box is None:
        return "icon renders nothing"
    image = image.crop(box)
    scale = ICON_LONG_SIDE / max(image.size)
    image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (ICON_BOX, ICON_BOX), (0, 0, 0, 0))
    canvas.paste(image, ((ICON_BOX - image.width) // 2, (ICON_BOX - image.height) // 2), image)
    canvas.save(target, optimize=True)
    return None


def build_room(room):
    raw, out = RAW / room, OUT / "rooms" / room
    # Every arrangement of a room type shows the same objects, so they share the
    # icons rendered for arrangement 1.
    icons_raw = RAW / f"{room.rpartition('_')[0]}_1" / "icons"
    for sub in ("objects", "icons"):
        (out / sub).mkdir(parents=True, exist_ok=True)
        for old in (out / sub).glob("*.png"):
            old.unlink()
    for name in ("full", "empty"):
        Image.open(raw / f"{name}.png").convert("RGB").save(out / f"{name}.jpg", quality=92, subsampling=0)
    width, height = Image.open(raw / "full.png").size
    objects, problems = [], []
    for entry in json.loads((raw / "objects.json").read_text()):
        i = entry["index"]
        sprite = Image.open(raw / "objects" / f"{i:02d}.png").convert("RGBA")
        # Solid enough to see. The same threshold is used for both images, so soft
        # edges on thin objects do not read as being blocked.
        alpha = sprite.getchannel("A").point(lambda v: 255 if v > 64 else 0)
        box = alpha.getbbox()
        if box is None:
            problems.append(f"{entry['label']}: renders nothing")
            continue
        mask = Image.open(raw / "masks" / f"{i:02d}.png").convert("RGBA").getchannel("A").point(lambda v: 255 if v > 64 else 0)
        whole = alpha.histogram()[255]
        seen = ImageChops.multiply(alpha, mask).histogram()[255]
        visible = seen / whole
        w, h = box[2] - box[0], box[3] - box[1]
        if visible < MIN_VISIBLE:
            problems.append(f"{entry['label']}: only {visible:.0%} visible")
        if box[0] < EDGE_MARGIN or box[1] < EDGE_MARGIN or box[2] > width - EDGE_MARGIN or box[3] > height - EDGE_MARGIN:
            problems.append(f"{entry['label']}: touches the image edge {box}")
        if min(w, h) < MIN_SIDE and max(w, h) < MIN_SIDE * 2:
            problems.append(f"{entry['label']}: too small ({w}x{h})")
        file = f"objects/{entry['id']}.png"
        sprite.crop(box).save(out / file, optimize=True)
        icon = f"icons/{entry['id']}.png"
        icon_problem = build_icon(icons_raw / f"{i:02d}.png", out / icon)
        if icon_problem:
            problems.append(f"{entry['label']}: {icon_problem}")
        objects.append({
            "id": entry["id"], "label": entry["label"], "file": file, "icon": icon,
            "center": [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2],
            "size": [w, h], "visible_fraction": round(visible, 3),
        })
    # Correct spots must be far enough apart that one placement cannot score two
    # objects, and a swap between neighbours is distinguishable from a near miss.
    tolerance_px = MIN_SPACING * width
    for a in range(len(objects)):
        for b in range(a + 1, len(objects)):
            ca, cb = objects[a]["center"], objects[b]["center"]
            distance = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
            if distance <= tolerance_px:
                problems.append(f"{objects[a]['label']} and {objects[b]['label']} are only {distance:.0f}px apart")
    (out / "room.json").write_text(json.dumps(
        {"room": room, "width": width, "height": height, "objects": objects}, indent=2))
    return problems


def check_arrangements(kind):
    """The same objects in the same order in every arrangement, and no object
    within twice the tolerance of where it stood in another arrangement."""
    problems = []
    rooms = [json.loads((OUT / "rooms" / f"{kind}_{k}" / "room.json").read_text()) for k in ARRANGEMENTS]
    ids = [[o["id"] for o in r["objects"]] for r in rooms]
    if any(i != ids[0] for i in ids):
        return [f"{kind}: arrangements do not hold the same objects in the same order"]
    limit = MIN_SPACING * rooms[0]["width"]
    for index, object_id in enumerate(ids[0]):
        spots = [r["objects"][index]["center"] for r in rooms]
        for a in range(len(spots)):
            for b in range(a + 1, len(spots)):
                d = ((spots[a][0] - spots[b][0]) ** 2 + (spots[a][1] - spots[b][1]) ** 2) ** 0.5
                if d <= limit:
                    problems.append(f"{kind}: {object_id} only moves {d:.0f}px between arrangements {a + 1} and {b + 1}")
    return problems


def build_transition():
    out = OUT / "transition"
    out.mkdir(parents=True, exist_ok=True)
    frames = sorted((RAW / "transition").glob("*.jpg"))
    for frame in frames:
        (out / frame.name).write_bytes(frame.read_bytes())
    return [] if len(frames) == 72 else [f"transition has {len(frames)} frames, expected 72"]


def main():
    problems = []
    for room in ROOMS:
        problems += [f"{room}: {p}" for p in build_room(room)]
    for kind in ROOM_TYPES:
        problems += check_arrangements(kind)
    problems += build_transition()
    for problem in problems:
        print("PROBLEM", problem)
    print("postprocess:", "FAILED" if problems else "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
