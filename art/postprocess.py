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


def build_room(room):
    raw, out = RAW / room, OUT / "rooms" / room
    (out / "objects").mkdir(parents=True, exist_ok=True)
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
        objects.append({
            "id": entry["id"], "label": entry["label"], "file": file,
            "center": [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2],
            "size": [w, h], "visible_fraction": round(visible, 3),
        })
    # Correct spots must be far enough apart that one placement cannot score two objects.
    tolerance_px = 0.05 * width
    for a in range(len(objects)):
        for b in range(a + 1, len(objects)):
            ca, cb = objects[a]["center"], objects[b]["center"]
            distance = ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5
            if distance <= tolerance_px:
                problems.append(f"{objects[a]['label']} and {objects[b]['label']} are only {distance:.0f}px apart")
    (out / "room.json").write_text(json.dumps(
        {"room": room, "width": width, "height": height, "objects": objects}, indent=2))
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
    for room in ("kitchen", "living_room"):
        problems += [f"{room}: {p}" for p in build_room(room)]
    problems += build_transition()
    for problem in problems:
        print("PROBLEM", problem)
    print("postprocess:", "FAILED" if problems else "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
