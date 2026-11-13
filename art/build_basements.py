"""Build and render the basement rooms in Blender.

  blender -b --python art/build_basements.py -- --room storage --mode preview
  blender -b --python art/build_basements.py -- --room storage --mode final

Modes:
  preview  small render with every spot marked (target spots pink, filler spots blue)
  final    the empty room at full size, plus spots.json: every spot's screen position,
           pixels per metre, shadow shape and the light measured there

Each room holds only furniture in 3D. Everything small (filler and the target photos)
is added later as a cutout by art/assemble_assets.py and the task itself.

The camera sits a little high and looks down, so the table in front is seen almost
from above and the shelves and floor behind from the side.
"""
import argparse
import json
import math
import pathlib
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from blender_kit import (PREVIEW, RAW, ROOM_BACK, ROOM_W, base_cabinet, box, camera, cylinder, flat, paint,  # noqa: E402
                         pbr, place, render_to, setup_render, shell, sink, socket, surface_below)

OUT_W, OUT_H = 1600, 900
CAMERA = ((0.0, -2.55, 2.0), (0.0, 0.6, 0.55), 27)
HALF = ROOM_W / 2
STUDIO_WHITE = 225.0  # how bright a white probe looks under the dataset's studio light (0-255)

spots = []  # dicts: id, role (target/filler), surface, point, max_w, max_h, filler


def spot(id_, surface, x, y, z=None, drop=2.4, w=0.5, h=0.5, role="target", filler=None):
    """A free patch where an object can stand. z None: the first surface below drop."""
    if z is None:
        z = surface_below(x, y, drop)
    spots.append({"id": id_, "role": role, "surface": surface, "point": (x, y, z), "max_w": w, "max_h": h,
                  "filler": filler})


def filler(name, surface, x, y, z=None, drop=2.4):
    spot(f"filler_{len(spots)}", surface, x, y, z, drop, w=9, h=9, role="filler", filler=name)


def basement_shell(floor="concrete_floor_worn_001", wall="concrete_block_wall", tint=(0.92, 0.9, 0.86)):
    wall_mat = paint("wall", tint) if wall == "paint" else pbr("wall", wall, 1.4, tint=tint)
    shell(pbr("floor", floor, 1.6), wall_mat, window=(-0.5, 0.5, 2.0, 2.4),
          hdri="symmetrical_garden_02", hdri_rot=20, ceiling_light=26.0, sun=2.0, sun_rot=170, sill_depth=0.3)
    camera(*CAMERA[:2], lens=CAMERA[2])
    place("mounted_fluorescent_lights", 0.0, 0.2, z=2.55)
    bpy.ops.object.light_add(type="AREA", location=(0.0, 0.2, 2.5))
    tube = bpy.context.active_object
    tube.data.shape, tube.data.size, tube.data.size_y = "RECTANGLE", 0.9, 0.5
    tube.data.energy = 140
    tube.data.color = (0.96, 0.98, 1.0)
    tube.visible_camera = False


def pipes():
    metal = flat("pipe", (0.42, 0.4, 0.37), 0.5, 0.6)
    cylinder("pipe_a", 0.0, ROOM_BACK - 0.08, 2.3 - HALF, 2.3 + HALF, 0.04, metal, rot_y=90)
    cylinder("pipe_b", 0.0, ROOM_BACK - 0.16, 2.42 - HALF, 2.42 + HALF, 0.025, metal, rot_y=90)


def workbench(x, y, top, width, depth):
    """Foreground table, seen almost from above."""
    wood = pbr("bench_top", "oak_veneer_01", 0.8)
    legs = flat("bench_leg", (0.22, 0.2, 0.18), 0.6)
    box("bench_top", x - width / 2, x + width / 2, y - depth / 2, y + depth / 2, top - 0.04, top, wood)
    for dx in (-width / 2 + 0.05, width / 2 - 0.05):
        for dy in (-depth / 2 + 0.05, depth / 2 - 0.05):
            box("bench_leg", x + dx - 0.03, x + dx + 0.03, y + dy - 0.03, y + dy + 0.03, 0, top - 0.04, legs)
    box("bench_shelf", x - width / 2 + 0.05, x + width / 2 - 0.05, y - depth / 2 + 0.05, y + depth / 2 - 0.05,
        0.18, 0.2, wood)


# ---------------------------------------------------------------- rooms
BENCH_Y, BENCH_TOP = -1.12, 0.78


def bench_spots(top=BENCH_TOP, y=BENCH_Y):
    """Four free patches on the foreground table, seen from above."""
    for i, (x, dy, w) in enumerate(((-0.6, 0.12, 0.6), (-0.12, -0.08, 0.6), (0.33, 0.14, 0.6), (0.72, -0.1, 0.6))):
        spot(f"bench_{i}", "table", x, y + dy, z=top, w=w, h=0.55)


def shelf_unit_spots(prefix, x, y, levels, w, h):
    """One spot per shelf level; levels are approximate board heights (the ray finds the board)."""
    for i, z in enumerate(levels):
        spot(f"{prefix}{i}", "shelf", x, y, drop=z + 0.12, w=w, h=h)


def build_storage():
    basement_shell()
    pipes()
    place("steel_frame_shelves_01", -1.65, ROOM_BACK - 0.27, z=0)
    place("worn_metal_rack", 1.72, ROOM_BACK - 0.32, z=0)
    place("cardboard_box_01", -2.0, 0.55, z=0, rot=10, scale=0.9)
    place("cardboard_box_01", -2.0, 0.55, drop=1.2, rot=-5, scale=0.7)
    place("cardboard_box_01", -1.95, -0.1, z=0, rot=-20, scale=0.8)
    place("plastic_crate_02", 2.0, 0.6, z=0, rot=80)
    place("plastic_crate_02", 2.0, 0.6, drop=1.0, rot=84)
    place("Barrel_02", 2.0, -0.35, z=0)
    place("old_tyre", -0.62, ROOM_BACK - 0.2, z=0, rot_x=90, rot=-8, scale=0.9)
    workbench(0.0, BENCH_Y, BENCH_TOP, 1.7, 0.72)
    socket(0.95, 0.35)
    shelf_unit_spots("shelf_a", -1.9, ROOM_BACK - 0.27, (0.45, 0.85, 1.3), 0.45, 0.36)
    shelf_unit_spots("shelf_b", -1.4, ROOM_BACK - 0.27, (0.45, 0.85), 0.4, 0.36)
    shelf_unit_spots("rack_", 1.62, ROOM_BACK - 0.32, (0.6, 1.05), 0.55, 0.4)
    spot("wall_a", "wall", -0.25, ROOM_BACK - 0.01, z=1.2, w=0.65, h=0.95)
    spot("wall_b", "wall", 0.85, ROOM_BACK - 0.01, z=1.2, w=0.55, h=0.95)
    spot("lean_a", "lean", 0.3, ROOM_BACK - 0.12, z=0, w=0.5, h=1.25)
    spot("lean_b", "lean", 1.0, ROOM_BACK - 0.12, z=0, w=0.4, h=1.2)
    spot("floor_back", "floor", -0.5, 1.0, z=0, w=0.75, h=1.0)
    spot("floor_left", "floor", -1.35, 0.55, z=0, w=0.6, h=0.95)
    spot("floor_right", "floor", 1.2, 0.65, z=0, w=0.6, h=0.6)
    spot("floor_mid", "floor", 0.45, 0.6, z=0, w=0.45, h=0.5)
    bench_spots()
    filler("multi_cleaner_5_litre", "shelf", -1.6, ROOM_BACK - 0.27, drop=0.57)
    filler("spray_paint_bottles", "shelf", -1.6, ROOM_BACK - 0.27, drop=1.42)
    filler("plastic_bottle_gallon", "shelf", 1.92, ROOM_BACK - 0.32, drop=0.72)
    filler("oil_tin", "shelf", 1.92, ROOM_BACK - 0.32, drop=1.17)
    filler("metal_jerrycan", "floor", 1.75, 1.05, z=0)
    filler("can_rusted", "table", 0.1, BENCH_Y + 0.22, z=BENCH_TOP)
    filler("garden_gloves_01", "table", -0.4, BENCH_Y - 0.22, z=BENCH_TOP)
    filler("wooden_bucket_01", "floor", 1.45, ROOM_BACK - 0.3, z=0)
    filler("trashbag", "floor", -1.95, -0.7, z=0)


def build_laundry():
    basement_shell(floor="garage_floor", wall="paint", tint=(0.5, 0.53, 0.5))
    pipes()
    body = flat("laundry_cabinet", (0.86, 0.86, 0.83), 0.4)
    top = flat("laundry_top", (0.55, 0.56, 0.55), 0.3)
    base_cabinet(-2.25, -0.95, ROOM_BACK - 0.62, ROOM_BACK, 0.9, body, top, doors=2)
    sink(-1.95, -1.4, ROOM_BACK - 0.5, ROOM_BACK - 0.12, 0.9, top)
    place("painted_wooden_shelves", 1.85, ROOM_BACK - 0.2, z=0)
    place("plastic_crate_03", 1.95, 0.55, z=0, rot=85)
    place("plastic_crate_03", 1.95, 0.55, drop=1.0, rot=88)
    place("plastic_crate_01", -2.0, 0.35, z=0, rot=15)
    place("plastic_crate_01", -2.0, 0.35, drop=1.0, rot=5)
    place("cardboard_box_01", -1.95, -0.45, z=0, rot=35, scale=0.75)
    line = flat("line", (0.85, 0.85, 0.85), 0.5)
    cylinder("line", -0.3, ROOM_BACK - 0.6, 2.05 - 0.9, 2.05 + 0.9, 0.004, line, rot_y=90)
    melamine = flat("melamine", (0.9, 0.9, 0.88), 0.35)
    legs = flat("table_leg", (0.3, 0.3, 0.32), 0.4, 0.8)
    box("fold_top", -0.85, 0.85, BENCH_Y - 0.36, BENCH_Y + 0.36, BENCH_TOP - 0.03, BENCH_TOP, melamine)
    for dx in (-0.78, 0.78):
        for dy in (-0.3, 0.3):
            box("fold_leg", dx - 0.02, dx + 0.02, BENCH_Y + dy - 0.02, BENCH_Y + dy + 0.02, 0, BENCH_TOP - 0.03, legs)
    socket(-0.6, 1.2)
    spot("counter_a", "table", -2.12, ROOM_BACK - 0.3, z=0.9, w=0.3, h=0.55)
    spot("counter_b", "table", -1.15, ROOM_BACK - 0.3, z=0.9, w=0.35, h=0.55)
    shelf_unit_spots("shelf_", 1.85, ROOM_BACK - 0.2, (0.4, 0.75), 0.42, 0.3)
    spot("wall_a", "wall", -0.2, ROOM_BACK - 0.01, z=1.2, w=0.65, h=0.95)
    spot("wall_b", "wall", 0.9, ROOM_BACK - 0.01, z=1.2, w=0.6, h=0.95)
    spot("lean_a", "lean", 0.35, ROOM_BACK - 0.12, z=0, w=0.5, h=1.25)
    spot("lean_b", "lean", -0.6, ROOM_BACK - 0.12, z=0, w=0.45, h=1.25)
    spot("floor_back", "floor", 0.95, 1.2, z=0, w=0.75, h=1.0)
    spot("floor_left", "floor", -1.25, 0.6, z=0, w=0.65, h=1.0)
    spot("floor_right", "floor", 1.3, 0.55, z=0, w=0.6, h=0.9)
    spot("floor_mid", "floor", -0.15, 0.55, z=0, w=0.5, h=0.55)
    bench_spots()
    filler("bleach_bottle", "table", -1.0, ROOM_BACK - 0.15, z=0.9)
    filler("multi_cleaner_bottle", "table", -2.2, ROOM_BACK - 0.12, z=0.9)
    filler("all_purpose_cleaner", "table", -1.62, ROOM_BACK - 0.15, z=0.9)
    filler("plastic_container", "floor", -2.0, -1.15, z=0)
    filler("dustpan", "lean", -0.95, ROOM_BACK - 0.1, z=0)
    filler("drain_cleaner", "table", 0.05, BENCH_Y + 0.2, z=BENCH_TOP)
    filler("leather_cleaner_can", "table", -0.45, BENCH_Y - 0.25, z=BENCH_TOP)
    filler("industrial_pastic_container", "floor", 1.9, -0.6, z=0)
    filler("binder_notebook", "shelf", 1.75, ROOM_BACK - 0.2, drop=1.22)


def build_workshop():
    basement_shell(floor="garage_floor", wall="brick_wall_001", tint=(0.85, 0.82, 0.78))
    pipes()
    place("WoodenTable_03", 0.0, ROOM_BACK - 0.3, z=0)
    board = flat("pegboard", (0.62, 0.5, 0.36), 0.8)
    box("pegboard", -0.65, 0.65, ROOM_BACK - 0.02, ROOM_BACK, 0.95, 1.55, board)
    place("steel_frame_shelves_02", -1.95, ROOM_BACK - 0.27, z=0)
    place("tool_cart", 1.75, 0.95, z=0, rot=-90)
    place("wooden_crate_02", -1.95, -0.2, z=0, rot=95, scale=0.8)
    place("plastic_crate_03", 2.0, -0.3, z=0, rot=20)
    place("wooden_ladder", 1.95, ROOM_BACK - 0.15, z=0, scale=0.85)
    dark = pbr("bench_dark", "plank_flooring_02", 0.9)
    legs = flat("bench_leg", (0.22, 0.2, 0.18), 0.6)
    box("near_top", -0.85, 0.85, BENCH_Y - 0.36, BENCH_Y + 0.36, BENCH_TOP - 0.05, BENCH_TOP, dark)
    for dx in (-0.78, 0.78):
        for dy in (-0.3, 0.3):
            box("near_leg", dx - 0.035, dx + 0.035, BENCH_Y + dy - 0.035, BENCH_Y + dy + 0.035, 0, BENCH_TOP - 0.05, legs)
    socket(1.0, 0.35)
    spot("back_bench_a", "table", -0.4, ROOM_BACK - 0.35, drop=1.2, w=0.45, h=0.5)
    spot("back_bench_b", "table", 0.35, ROOM_BACK - 0.35, drop=1.2, w=0.45, h=0.5)
    shelf_unit_spots("shelf_", -1.95, ROOM_BACK - 0.27, (0.45, 0.85, 1.3), 0.45, 0.36)
    spot("cart_top", "table", 1.75, 0.95, drop=1.3, w=0.5, h=0.5)
    spot("wall_a", "wall", -1.05, ROOM_BACK - 0.01, z=1.2, w=0.55, h=0.95)
    spot("wall_peg", "wall", 0.0, ROOM_BACK - 0.03, z=1.2, w=0.6, h=0.95)
    spot("wall_b", "wall", 1.0, ROOM_BACK - 0.01, z=1.2, w=0.55, h=0.95)
    spot("lean_a", "lean", -1.2, ROOM_BACK - 0.12, z=0, w=0.5, h=1.25)
    spot("lean_b", "lean", 1.05, ROOM_BACK - 0.12, z=0, w=0.45, h=1.25)
    spot("floor_back", "floor", -0.95, 1.05, z=0, w=0.75, h=1.0)
    spot("floor_left", "floor", -1.3, 0.5, z=0, w=0.6, h=1.0)
    spot("floor_right", "floor", 1.05, 0.55, z=0, w=0.6, h=0.9)
    spot("floor_mid", "floor", 0.3, 0.75, z=0, w=0.5, h=0.5)
    bench_spots()
    filler("small_oil_can_01", "table", 0.0, ROOM_BACK - 0.25, drop=1.2)
    filler("lubricant_spray", "table", 0.65, ROOM_BACK - 0.3, drop=1.2)
    filler("cleaner_tin_01", "shelf", -1.9, ROOM_BACK - 0.27, drop=0.57)
    filler("spray_paint_bottles_02", "shelf", -2.0, ROOM_BACK - 0.27, drop=0.97)
    filler("propane_tank", "floor", 2.0, 0.35, z=0)
    filler("plastic_jerrycan", "floor", -0.35, 1.35, z=0)
    filler("russian_food_cans_01", "table", 0.15, BENCH_Y + 0.25, z=BENCH_TOP)
    filler("medical_tape", "table", -0.38, BENCH_Y - 0.27, z=BENCH_TOP)
    filler("metal_jerrycan_green", "floor", 1.85, -1.0, z=0)


def build_practice():
    basement_shell(floor="concrete_floor_worn_001", wall="paint", tint=(0.55, 0.5, 0.43))
    place("steel_frame_shelves_02", -1.2, ROOM_BACK - 0.27, z=0)
    place("wooden_crate_01", 1.4, ROOM_BACK - 0.3, z=0, rot=5)
    place("cardboard_box_01", 1.9, 0.4, z=0, rot=20, scale=0.8)
    workbench(0.0, BENCH_Y, BENCH_TOP, 1.7, 0.72)
    shelf_unit_spots("shelf_", -1.2, ROOM_BACK - 0.27, (0.45, 0.85, 1.3), 0.45, 0.36)
    spot("crate_top", "table", 1.4, ROOM_BACK - 0.3, drop=1.0, w=0.5, h=0.5)
    bench_spots()
    filler("planter_pot_clay", "table", 0.1, BENCH_Y + 0.2, z=BENCH_TOP)
    filler("compost_bag_02", "floor", 0.4, 1.2, z=0)
    filler("wooden_bucket_01", "floor", -0.3, 0.6, z=0)
    filler("small_lpg_tank", "floor", 1.9, -0.6, z=0)


BUILDERS = {"storage": build_storage, "laundry": build_laundry, "workshop": build_workshop,
            "practice": build_practice}


# ---------------------------------------------------------------- export
def project(point):
    scene, cam = bpy.context.scene, bpy.context.scene.camera
    p = world_to_camera_view(scene, cam, Vector(point))
    return p.x * OUT_W, (1 - p.y) * OUT_H


def spot_record(s):
    cam = bpy.context.scene.camera
    point = Vector(s["point"])
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    anchor = point
    x, y = project(anchor)
    a, b = project(anchor - right * 0.25), project(anchor + right * 0.25)
    px_per_m = math.dist(a, b) / 0.5
    r = 0.15
    xs = [project(point + Vector(d))[0] for d in ((-r, 0, 0), (r, 0, 0))]
    ys = [project(point + Vector(d))[1] for d in ((0, -r, 0), (0, r, 0))]
    squash = abs(ys[1] - ys[0]) / max(1e-6, abs(xs[1] - xs[0]))
    record = {"id": s["id"], "surface": s["surface"], "x": round(x, 1), "y": round(y, 1),
              "px_per_m": round(px_per_m, 2), "max_w_m": s["max_w"], "max_h_m": s["max_h"],
              "squash": round(squash, 3)}
    if s["role"] == "filler":
        record["filler"] = s["filler"]
    return record


def probe_points():
    """Where to measure the light: just above each spot, or just off the wall."""
    out = []
    for s in spots:
        x, y, z = s["point"]
        out.append((x, y - 0.07, z) if s["surface"] == "wall" else (x, y, z + 0.1))
    return out


def measure_light(samples=48):
    """Render small white spheres at every spot and read how bright each looks."""
    import numpy as np
    white = flat("probe", (0.8, 0.8, 0.8), 0.9)
    probes = []
    for i, point in enumerate(probe_points()):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=point)
        ball = bpy.context.active_object
        ball.data.materials.append(white)
        ball.visible_shadow = False
        probes.append(ball)
    setup_render(OUT_W // 2, OUT_H // 2, samples)
    target = PREVIEW / "_probe.png"
    render_to(target)
    image = bpy.data.images.load(str(target), check_existing=False)
    pixels = np.array(image.pixels[:]).reshape(OUT_H // 2, OUT_W // 2, 4)[::-1]  # top row first
    lights = []
    for point in probe_points():
        x, y = project(point)
        cx, cy = int(x / 2), int(y / 2)
        patch = pixels[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2, :3].reshape(-1, 3).mean(axis=0) * 255
        lights.append([round(float(min(1.1, max(0.35, v / STUDIO_WHITE))), 3) for v in patch])
    for ball in probes:
        bpy.data.objects.remove(ball)
    return lights


def mark_spots():
    pink = flat("spot_target", (1.0, 0.05, 0.4), 0.4, emit=2.0)
    blue = flat("spot_filler", (0.1, 0.4, 1.0), 0.4, emit=2.0)
    for s in spots:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=Vector(s["point"]) + Vector((0, 0, 0.035)))
        bpy.context.active_object.data.materials.append(pink if s["role"] == "target" else blue)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", required=True, choices=sorted(BUILDERS))
    parser.add_argument("--mode", default="preview", choices=["preview", "final"])
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spots.clear()
    BUILDERS[args.room]()
    if args.mode == "preview":
        mark_spots()
        setup_render(960, 540, 32)
        render_to(PREVIEW / f"{args.room}.png")
        return
    out = RAW / "basements" / args.room
    lights = measure_light()
    records = [spot_record(s) | {"light": light} for s, light in zip(spots, lights)]
    (out).mkdir(parents=True, exist_ok=True)
    (out / "spots.json").write_text(json.dumps({"width": OUT_W, "height": OUT_H, "spots": records}, indent=1))
    setup_render(OUT_W, OUT_H, args.samples)
    if not (out / "empty.png").exists():
        render_to(out / "empty.png")


if __name__ == "__main__":
    main()
