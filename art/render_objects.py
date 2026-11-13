"""Studio shots of the made objects (decoys, practice objects, room filler).

Each object is shot alone in the style of the dataset photos: a soft, even product
light, seen a little from above and turned to a three-quarter view, on a clear
background so it can be cut out like the photos. Run inside Blender:

  blender -b --python art/render_objects.py -- [--only NAME ...] [--samples 64]

Writes art/_downloads/raw/objects/<name>.png and <name>.json (metres per pixel).
Resumes: existing pictures are skipped.
"""
import argparse
import csv
import json
import math
import pathlib
import sys

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from blender_kit import RAW, place, placed, render_to, setup_render, world_bbox  # noqa: E402

SIZE = 1024
ELEVATION = math.radians(18)
OUT = RAW / "objects"


def shoot(row, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    placed.clear()
    pick = [p for p in row["pick"].split("|") if p] or None
    rec = place(row["model"], 0, 0, z=0, pick=pick)
    low, high = world_bbox(rec["meshes"])
    width, depth = high.x - low.x, high.y - low.y
    # Flat-fronted things (frames, boards) face the camera; the rest turn three-quarters.
    turn = 12 if depth < 0.2 * width else 32
    root = next(o for o in bpy.data.objects if o.name.startswith("root_"))
    root.rotation_euler.z += math.radians(turn)
    bpy.context.view_layer.update()
    low, high = world_bbox(rec["meshes"])
    centre = (low + high) / 2
    size = max(high - low)
    distance = size * 8
    bpy.ops.object.camera_add(location=(centre.x, centre.y - distance * math.cos(ELEVATION),
                                        centre.z + distance * math.sin(ELEVATION)))
    cam = bpy.context.active_object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = size * 1.25
    cam.data.clip_end = distance * 4
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    world = bpy.data.worlds.new("studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
    bpy.context.scene.world = world
    # Big soft key from front left and above, a weaker fill from the right, a top light.
    for (dx, dy, dz), power, scale in (((-1.6, -2.6, 2.4), 90, 5), ((2.2, -2.0, 0.8), 35, 5), ((0, 0.3, 3.2), 45, 4)):
        bpy.ops.object.light_add(type="AREA", location=(centre.x + dx * size, centre.y + dy * size,
                                                        centre.z + dz * size))
        light = bpy.context.active_object
        light.data.size = size * scale
        light.data.energy = power * size * size + 2
        light.rotation_euler = (centre - light.location).to_track_quat("-Z", "Y").to_euler()

    setup_render(SIZE, SIZE, samples)
    scene = bpy.context.scene
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.45
    render_to(OUT / f"{row['name']}.png", transparent=True, color_mode="RGBA")
    (OUT / f"{row['name']}.json").write_text(json.dumps({"m_per_px": cam.data.ortho_scale / SIZE}))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args(argv)
    with open(pathlib.Path(__file__).parent / "made_objects.csv", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if args.only and row["name"] not in args.only:
            continue
        if (OUT / f"{row['name']}.png").exists() and not args.only:
            continue
        shoot(row, args.samples)


if __name__ == "__main__":
    main()
