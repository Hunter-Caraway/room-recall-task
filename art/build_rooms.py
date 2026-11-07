"""Build and render the study rooms in Blender.

Run through render_all.sh, or directly:
  blender -b --python art/build_rooms.py -- --scene kitchen --mode preview

Modes:
  preview     small render of the furnished room, for checking layout
  final       furnished and empty room at full size, plus one cutout per scored object
  transition  doorway walk frames (use --scene hallway)
"""
import argparse
import json
import math
import pathlib
import sys

import bpy
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parent
MODELS = ROOT / "_downloads" / "models"
TEXTURES = ROOT / "_downloads" / "textures"
RAW = ROOT / "_downloads" / "raw"
PREVIEW = ROOT / "_preview"

ROOM_W, ROOM_BACK, ROOM_FRONT, ROOM_H = 4.6, 1.9, -2.7, 2.6
OUT_W, OUT_H = 1600, 900

placed = []  # one record per imported model


# ---------------------------------------------------------------- materials
def pbr(name, tex, scale=1.0, tint=None, rough=None):
    """Tiled PBR material using box projection, so it fits any box without UVs."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / scale, 1 / scale, 1 / scale)
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def image(file, colorspace):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(TEXTURES / tex / file), check_existing=True)
        node.image.colorspace_settings.name = colorspace
        node.projection = "BOX"
        node.projection_blend = 0.15
        links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    color = image("Diffuse.jpg", "sRGB")
    if tint:
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        links.new(color.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = (*tint, 1)
        links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        links.new(color.outputs["Color"], bsdf.inputs["Base Color"])
    if rough is None:
        links.new(image("Rough.jpg", "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = rough
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = 0.6
    links.new(image("nor_gl.jpg", "Non-Color").outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def flat(name, color, rough=0.5, metal=0.0, emit=0.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat


def paint(name, color):
    """Painted wall: flat color with a faint roller texture."""
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.75
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 180
    noise.inputs["Detail"].default_value = 4
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    links.new(noise.outputs[0], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ---------------------------------------------------------------- geometry
def box(name, x0, x1, y0, y1, z0, z1, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = (x1 - x0, y1 - y0, z1 - z0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_flat()
    obj.data.materials.append(mat)
    return obj


def world_bbox(meshes):
    points = [m.matrix_world @ Vector(c) for m in meshes for c in m.bound_box]
    low = Vector(min(p[i] for p in points) for i in range(3))
    high = Vector(max(p[i] for p in points) for i in range(3))
    return low, high


def surface_below(x, y, start):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, location, *_ = bpy.context.scene.ray_cast(depsgraph, Vector((x, y, start)), Vector((0, 0, -1)))
    return location.z if hit else 0.0


def place(name, x, y, z=None, drop=2.5, rot=0.0, rot_x=0.0, scale=1.0, pick=None,
          role="clutter", label=None, lift=0.0):
    """Import a model and stand it on the first surface under (x, y, drop)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(MODELS / name / f"{name}.gltf"))
    new = set(bpy.data.objects) - before
    if pick:
        for obj in list(new):
            if obj.type == "MESH" and not any(p in obj.name for p in pick):
                new.discard(obj)
                bpy.data.objects.remove(obj)
    root = bpy.data.objects.new(f"root_{name}", None)
    bpy.context.collection.objects.link(root)
    for obj in new:
        if obj.parent is None:
            obj.parent = root
    root.scale = scale if isinstance(scale, tuple) else (scale,) * 3
    root.rotation_euler = (math.radians(rot_x), 0, math.radians(rot))
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    low, high = world_bbox(meshes)
    if z is None:
        for mesh in meshes:  # do not let the model hit itself
            mesh.hide_viewport = True
        z = surface_below(x, y, drop)
        for mesh in meshes:
            mesh.hide_viewport = False
    root.location = Vector((x - (low.x + high.x) / 2, y - (low.y + high.y) / 2, z - low.z + 0.001 + lift))
    bpy.context.view_layer.update()
    record = {"name": name, "meshes": meshes, "role": role, "label": label or name}
    placed.append(record)
    return record


def shell(floor_mat, wall_mat, window=None, ceiling_light=75.0, sun=3.0):
    """Closed room with one window in the back wall: window = (x0, x1, z0, z1)."""
    half = ROOM_W / 2
    t = 0.2
    box("floor", -half - t, half + t, ROOM_FRONT - t, ROOM_BACK + t, -t, 0, floor_mat)
    box("ceiling", -half - t, half + t, ROOM_FRONT - t, ROOM_BACK + t, ROOM_H, ROOM_H + t,
        flat("ceiling", (0.9, 0.89, 0.86), 0.9))
    box("wall_left", -half - t, -half, ROOM_FRONT - t, ROOM_BACK + t, 0, ROOM_H, wall_mat)
    box("wall_right", half, half + t, ROOM_FRONT - t, ROOM_BACK + t, 0, ROOM_H, wall_mat)
    box("wall_front", -half, half, ROOM_FRONT - t, ROOM_FRONT, 0, ROOM_H, wall_mat)
    skirting = flat("skirting", (0.75, 0.73, 0.69), 0.45)
    box("skirt_l", -half, -half + 0.015, ROOM_FRONT, ROOM_BACK, 0, 0.1, skirting)
    box("skirt_r", half - 0.015, half, ROOM_FRONT, ROOM_BACK, 0, 0.1, skirting)
    box("skirt_b", -half, half, ROOM_BACK - 0.015, ROOM_BACK, 0, 0.1, skirting)
    back = (ROOM_BACK, ROOM_BACK + t)
    if window:
        x0, x1, z0, z1 = window
        box("wall_b1", -half, x0, *back, 0, ROOM_H, wall_mat)
        box("wall_b2", x1, half, *back, 0, ROOM_H, wall_mat)
        box("wall_b3", x0, x1, *back, 0, z0, wall_mat)
        box("wall_b4", x0, x1, *back, z1, ROOM_H, wall_mat)
        frame = flat("window_frame", (0.8, 0.79, 0.76), 0.4)
        f = 0.045
        for i, (a, b, c, d) in enumerate([
            (x0, x1, z0, z0 + f), (x0, x1, z1 - f, z1),
            (x0, x0 + f, z0 + f, z1 - f), (x1 - f, x1, z0 + f, z1 - f),
            ((x0 + x1) / 2 - f / 2, (x0 + x1) / 2 + f / 2, z0 + f, z1 - f),
        ]):
            box(f"window_frame_{i}", a, b, ROOM_BACK + 0.05, ROOM_BACK + 0.12, c, d, frame)
        box("window_sill", x0 - 0.05, x1 + 0.05, ROOM_BACK - 0.06, ROOM_BACK + 0.12, z0 - 0.03, z0, frame)
    else:
        box("wall_b", -half, half, *back, 0, ROOM_H, wall_mat)

    world = bpy.data.worlds.new("outdoors")
    world.use_nodes = True
    env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(ROOT / "_downloads" / "hdri" / "symmetrical_garden_02.hdr"))
    world.node_tree.links.new(env.outputs["Color"], world.node_tree.nodes["Background"].inputs["Color"])
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.6
    bpy.context.scene.world = world

    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(62), 0, math.radians(165)))
    bpy.context.active_object.data.energy = sun
    bpy.context.active_object.data.angle = math.radians(4)
    bpy.context.active_object.data.color = (1.0, 0.93, 0.82)

    # Soft ceiling lights. Hidden from the camera; they stand in for room light.
    for x in (-1.2, 1.2):
        bpy.ops.object.light_add(type="AREA", location=(x, -0.3, ROOM_H - 0.02))
        light = bpy.context.active_object
        light.data.shape = "RECTANGLE"
        light.data.size, light.data.size_y = 2.2, 3.0
        light.data.energy = ceiling_light
        light.data.color = (1.0, 0.95, 0.87)
        light.visible_camera = False


def camera(location, target, lens=22):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.data.lens = lens
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def base_cabinet(x0, x1, y0, y1, height, mat_body, mat_top, doors):
    box("cab_body", x0, x1, y0, y1, 0.09, height - 0.04, mat_body)
    box("cab_kick", x0, x1, y0 + 0.05, y1, 0, 0.09, flat("kick", (0.08, 0.08, 0.08), 0.6))
    box("cab_top", x0 - 0.01, x1 + 0.01, y0 - 0.02, y1, height - 0.04, height, mat_top)
    width = (x1 - x0) / doors
    handle = flat("handle", (0.55, 0.55, 0.55), 0.3, 1.0)
    for i in range(doors):
        a, b = x0 + i * width + 0.006, x0 + (i + 1) * width - 0.006
        box(f"door_{i}", a, b, y0 - 0.018, y0, 0.11, height - 0.06, mat_body)
        mid = (a + b) / 2
        box(f"pull_{i}", mid - 0.07, mid + 0.07, y0 - 0.045, y0 - 0.02, height - 0.14, height - 0.125, handle)


# ---------------------------------------------------------------- rooms
def build_kitchen():
    shell(pbr("floor_tile", "floor_tiles_06", 1.6), paint("kitchen_wall", (0.72, 0.74, 0.62)),
          window=(0.3, 1.45, 1.2, 2.25))
    camera((0.0, -2.5, 1.85), (0.0, 1.0, 0.72))

    half = ROOM_W / 2
    front_y = ROOM_BACK - 0.62
    body = pbr("cabinet", "kitchen_wood", 1.0, tint=(0.8, 0.77, 0.7))
    stone = pbr("counter", "marble_01", 1.2, rough=0.22)
    base_cabinet(-1.55, -0.47, front_y, ROOM_BACK, 0.92, body, stone, 2)
    base_cabinet(0.03, half, front_y, ROOM_BACK, 0.92, body, stone, 4)
    place("electric_stove", -0.22, ROOM_BACK - 0.33, z=0)

    tile = pbr("splash", "long_white_tiles", 0.7, rough=0.15)
    box("splash_l", -1.55, 0.3, ROOM_BACK - 0.012, ROOM_BACK, 0.92, 1.4, tile)
    box("splash_r", 1.45, half, ROOM_BACK - 0.012, ROOM_BACK, 0.92, 1.4, tile)
    steel = flat("hood", (0.5, 0.5, 0.5), 0.3, 1.0)
    box("hood", -0.52, 0.08, ROOM_BACK - 0.45, ROOM_BACK, 1.72, 1.86, steel)
    box("hood_flue", -0.34, -0.1, ROOM_BACK - 0.28, ROOM_BACK, 1.86, ROOM_H, steel)

    plank = pbr("plank", "oak_veneer_01", 0.9)
    box("shelf_l1", -1.55, -0.6, ROOM_BACK - 0.3, ROOM_BACK, 1.46, 1.5, plank)
    box("shelf_l2", -1.55, -0.6, ROOM_BACK - 0.3, ROOM_BACK, 1.92, 1.96, plank)
    box("shelf_r1", 1.55, half, ROOM_BACK - 0.3, ROOM_BACK, 1.5, 1.54, plank)
    box("shelf_r2", 1.55, half, ROOM_BACK - 0.3, ROOM_BACK, 1.95, 1.99, plank)

    handle = flat("handle", (0.55, 0.55, 0.55), 0.3, 1.0)
    box("fridge", -2.3, -1.6, ROOM_BACK - 0.68, ROOM_BACK, 0.02, 1.9, flat("fridge", (0.62, 0.64, 0.65), 0.28, 0.35))
    box("fridge_gap", -2.3, -1.6, ROOM_BACK - 0.695, ROOM_BACK - 0.68, 1.22, 1.235, flat("kick", (0.08, 0.08, 0.08), 0.6))
    box("fridge_h1", -1.72, -1.68, ROOM_BACK - 0.74, ROOM_BACK - 0.69, 1.3, 1.65, handle)
    box("fridge_h2", -1.72, -1.68, ROOM_BACK - 0.74, ROOM_BACK - 0.69, 0.75, 1.15, handle)

    place("dining_table", 0.05, -0.2, z=0, scale=(0.6, 0.62, 1.0))
    place("dining_chair_02", -0.95, -0.2, z=0, rot=-90)
    place("dining_chair_02", 1.05, -0.2, z=0, rot=90)
    place("painted_wooden_cabinet", half - 0.34, 0.62, z=0, rot=-90, scale=(1.0, 1.0, 0.86))
    place("wooden_display_shelves_01", -half + 0.21, 0.55, z=0, rot=180)
    place("metal_trash_can", -half + 0.3, -0.45, z=0, pick=["metal_trash_can", "handle"], scale=0.62)

    # Scored: every object is a different thing that could plausibly go elsewhere.
    s = dict(role="scored")
    place("wooden_bowl_01", -0.3, -0.42, label="wooden bowl", **s)
    place("wooden_cutting_board", 0.25, 0.08, rot=20, label="cutting board", **s)
    place("tea_set_01", 0.55, -0.48, pick=["teapot"], scale=1.3, rot=30, label="teapot", **s)
    place("pot_enamel_01", -0.22, ROOM_BACK - 0.28, drop=1.6, label="enamel pot", **s)
    place("vintage_electric_kettle", 0.58, ROOM_BACK - 0.3, drop=1.1, rot=-20, label="kettle", **s)
    place("bananas", 2.0, ROOM_BACK - 0.3, drop=1.1, pick=["bunch"], scale=1.25, label="bananas", **s)
    place("wicker_basket_01", -0.82, ROOM_BACK - 0.38, drop=1.1, label="wicker basket", **s)
    place("plastic_thermos", 1.55, ROOM_BACK - 0.28, drop=1.1, label="thermos", **s)
    place("alarm_clock_01", 2.08, ROOM_BACK - 0.14, drop=1.9, scale=1.1, label="alarm clock", **s)
    place("jug_01", -0.85, ROOM_BACK - 0.15, drop=1.9, label="jug", **s)
    place("carved_wooden_plate", half - 0.34, 0.9, drop=1.5, label="carved plate", **s)
    place("ceramic_vase_01", half - 0.34, 0.32, drop=1.5, label="ceramic vase", **s)
    place("multi_cleaner_bottle", -1.46, ROOM_BACK - 0.3, drop=1.1, scale=1.1, label="spray bottle", **s)
    place("watering_can_metal_01", -1.5, 0.85, z=0, rot=60, scale=1.1, label="watering can", **s)
    place("brass_pan_01", -1.25, ROOM_BACK - 0.15, drop=1.9, rot=90, label="brass pan", **s)

    # Unscored clutter stays visible when the room blinks empty.
    place("food_apple_01", 0.02, -0.52)
    place("food_pears_asian_01", -0.05, 0.02, pick=["_a", "_b", "_d"])
    place("carrot_cake", -0.4, 0.02)
    place("hamburger_buns", 0.92, ROOM_BACK - 0.35, drop=1.1, scale=0.8)
    place("lemon", 1.2, ROOM_BACK - 0.42, drop=1.1)
    place("yellow_onion", 1.15, ROOM_BACK - 0.25, drop=1.1)
    place("food_lime_01", 1.27, ROOM_BACK - 0.3, drop=1.1)
    place("sweet_potato", 1.78, ROOM_BACK - 0.42, drop=1.1, scale=0.9)
    place("food_avocado_01", -0.56, ROOM_BACK - 0.5, drop=1.1)
    place("drain_cleaner", -0.6, ROOM_BACK - 0.1, drop=1.1, scale=0.8)
    place("long_life_food", -1.18, ROOM_BACK - 0.12, drop=1.44, pick=["beans", "milk", "tomatoes"])
    place("russian_food_cans_01", 1.95, ROOM_BACK - 0.15, drop=2.3, scale=1.6)
    place("all_purpose_cleaner", 1.72, ROOM_BACK - 0.15, drop=1.9, scale=0.8)
    place("brass_pot_01", -1.0, ROOM_BACK - 0.16, drop=2.4, scale=0.8)
    place("wooden_bowl_02", -1.38, ROOM_BACK - 0.15, drop=2.4, scale=0.8)
    place("plastic_bottle_gallon", 1.78, ROOM_BACK - 0.16, drop=2.4, scale=0.55)
    place("metal_jug", 2.15, ROOM_BACK - 0.16, drop=2.4, scale=0.7)
    place("wine_bottles_01", -half + 0.2, 0.55, drop=0.75, rot=90, scale=0.9, pick=["alsace", "bordeaux", "burgundy"])
    place("ceramic_pot", -half + 0.2, 0.3, drop=1.15, scale=0.8)
    place("potted_plant_02", -half + 0.2, 0.75, drop=2.0, scale=0.55)
    place("wooden_bucket_01", half - 0.3, -0.15, z=0, pick=["bucket"], scale=0.7)
    place("plastic_broom", half - 0.2, -0.65, z=0, rot=90, scale=0.85)
    place("dustpan", 1.55, 0.72, z=0, rot=30)
    place("bleach_bottle", 1.02, ROOM_BACK - 0.14, drop=1.1)
    place("hanging_picture_frame_03", half - 0.015, 0.55, z=1.5, rot=-90, scale=0.6)
    place("fancy_picture_frame_02", -half + 0.015, -0.5, z=1.25, rot=90, scale=0.7)
    place("croissant", 0.12, -0.28, rot=35)
    place("food_kiwi_01", -0.12, -0.62)
    place("clipboard", -0.48, -0.18, scale=0.7, rot=-15)
    place("planter_pot_clay", 0.62, ROOM_BACK + 0.0, drop=1.45, scale=0.45)
    place("brass_goblets", 1.35, ROOM_BACK - 0.15, drop=1.1, scale=0.55)
    place("metal_jug", -half + 0.2, 0.3, drop=0.75, scale=0.6)
    place("plastic_bottle_gallon", -half + 0.2, 0.75, drop=0.42, scale=0.45)
    place("wooden_candlestick", -half + 0.2, 0.75, drop=1.15, scale=0.7)
    place("stationery_supplies", -half + 0.2, 0.3, drop=1.55, scale=0.8)
    place("brass_pot_01", 1.65, 0.9, z=0, scale=0.75)
    place("wicker_basket_02", 1.5, -1.0, z=0, scale=1.1, rot=20)


def build_living_room():
    shell(pbr("floor_parquet", "herringbone_parquet", 1.4), paint("living_wall", (0.58, 0.66, 0.72)),
          window=(-0.15, 1.25, 1.1, 2.25))
    camera((0.0, -2.5, 1.85), (0.0, 1.0, 0.62))

    half = ROOM_W / 2
    rug = pbr("rug", "fabric_pattern_07", 0.6, tint=(0.85, 0.72, 0.62), rough=0.95)
    box("rug", -1.25, 1.55, -0.85, 1.05, 0, 0.012, rug)

    place("wooden_bookshelf_worn", -1.5, ROOM_BACK - 0.3, z=0)
    place("Sofa_01", 0.4, ROOM_BACK - 0.42, z=0, scale=1.15)
    place("side_table_01", 1.62, ROOM_BACK - 0.27, z=0)
    place("ClassicConsole_01", half - 0.31, 0.65, z=0, rot=-90)
    place("ArmChair_01", -1.72, 0.2, z=0, rot=-65, scale=0.9)
    place("coffee_table_round_01", 0.35, 0.15, z=0, scale=(0.82, 0.82, 1.0))
    place("Ottoman_01", -0.78, -0.42, z=0, scale=0.7, rot=10)
    place("vintage_grandfather_clock_01", -0.5, ROOM_BACK - 0.25, z=0, scale=0.9)
    place("throw_pillows_01", 0.05, ROOM_BACK - 0.5, drop=1.0, pick=["pillow02"], scale=0.7)
    place("calathea_orbifolia_01", 2.05, -1.0, z=0, scale=0.7)

    s = dict(role="scored")
    place("boombox", half - 0.3, 1.14, drop=1.5, rot=-90, scale=0.62, label="boombox", **s)
    place("binoculars", 0.05, 0.28, drop=1.0, rot=40, scale=1.3, label="binoculars", **s)
    place("mantel_clock_01", half - 0.34, 0.1, drop=1.5, rot=-90, label="mantel clock", **s)
    place("desk_lamp_arm_01", 1.62, ROOM_BACK - 0.27, drop=1.2, rot=200, scale=0.8, label="desk lamp", **s)
    place("Camera_01", 0.72, -0.05, drop=1.0, rot=20, scale=1.2, label="camera", **s)
    place("horse_statue_01", -0.78, -0.42, drop=1.0, rot=30, scale=0.7, label="horse statue", **s)
    place("concrete_cat_statue", -0.95, 0.72, z=0.012, rot=130, scale=1.3, label="cat statue", **s)
    place("antique_ceramic_vase_01", -1.05, ROOM_BACK - 0.3, drop=1.4, scale=0.7, label="antique vase", **s)
    place("brass_candleholders", -1.95, ROOM_BACK - 0.3, drop=1.45, pick=["candleholder_02"], scale=0.8, label="candleholder", **s)
    place("vintage_suitcase", 1.38, -0.12, z=0.012, rot=-25, pick=["suitcase_01"], scale=0.65, label="suitcase", **s)
    place("magnifying_glass_01", 0.42, 0.5, drop=1.0, rot_x=90, rot=50, scale=1.3, label="magnifying glass", **s)
    place("rubber_duck_toy", -1.5, ROOM_BACK - 0.3, drop=1.05, scale=0.6, label="rubber duck", **s)
    place("carved_wooden_elephant", -1.5, ROOM_BACK - 0.3, drop=1.82, scale=1.7, label="carved elephant", **s)
    place("potted_plant_04", half - 0.3, 0.62, drop=1.5, scale=1.2, label="small plant", **s)
    place("Ukulele_01", 0.62, ROOM_BACK - 0.48, drop=1.0, rot_x=90, rot=75, lift=0.025, label="ukulele", **s)

    place("book_encyclopedia_set_01", -1.55, ROOM_BACK - 0.28, drop=0.72)
    place("stationery_supplies", 0.68, 0.42, drop=1.0, scale=0.9)
    place("office_notepads", 0.32, -0.12, drop=1.0, pick=["yellow_pad"], scale=0.9, rot=15)
    place("clipboard", -1.15, ROOM_BACK - 0.3, drop=0.72, scale=0.8)
    place("wicker_basket_02", -1.55, -0.62, z=0, scale=1.0)
    place("ceramic_vase_03", -1.95, ROOM_BACK - 0.25, drop=1.05, scale=0.7)
    place("standing_picture_frame_02", 1.42, ROOM_BACK - 0.14, drop=1.2)
    place("hanging_picture_frame_03", half - 0.015, 0.45, z=1.35, rot=-90, scale=0.85)
    place("fancy_picture_frame_02", -half + 0.015, 0.45, z=1.3, rot=90)
    place("brass_goblets", -1.92, ROOM_BACK - 0.3, drop=1.05, scale=0.5)
    place("ceramic_pot", -1.05, ROOM_BACK - 0.3, drop=0.42, scale=0.7)
    place("book_encyclopedia_set_01", -1.5, ROOM_BACK - 0.28, drop=0.42, scale=0.9)
    place("office_notepads", -1.85, ROOM_BACK - 0.3, drop=0.42, pick=["a4_stack"], scale=1.0)
    place("wall_clock", 1.75, ROOM_BACK - 0.03, z=1.5)
    place("ornate_mirror_01", -half + 0.015, -0.75, z=1.05, rot=90)
    place("tea_set_01", 0.48, 0.1, drop=1.0, pick=["cup_small_01", "saucer_circular_04"])
    place("chess_set", -1.9, ROOM_BACK - 0.3, drop=0.72, scale=0.45)
    place("vintage_oil_lamp", -1.95, ROOM_BACK - 0.3, drop=1.82, scale=0.6)
    place("lambis_shell", -1.05, ROOM_BACK - 0.3, drop=1.82, scale=0.8)
    place("round_spectacles", 0.22, 0.02, drop=1.0, rot=-20)
    place("wooden_candlestick", 1.78, ROOM_BACK - 0.42, drop=1.2, scale=0.8)
    place("pocket_watch", 0.1, -0.02, drop=1.0, scale=1.2)


def build_hallway():
    """Neutral corridor used for every transition, so all transitions are identical."""
    wall = paint("hall_wall", (0.66, 0.63, 0.57))
    floor = pbr("floor_h", "laminate_floor_02", 1.6)
    trim = flat("trim", (0.78, 0.77, 0.73), 0.45)
    w, length, h = 0.8, 11.0, 2.5
    box("floor", -3, 3, -1, length, -0.2, 0, floor)
    box("ceiling", -3, 3, -1, length, h, h + 0.2, flat("ceiling", (0.9, 0.89, 0.86), 0.9))
    box("wall_l", -w - 0.2, -w, -1, 6, 0, h, wall)
    box("wall_r", w, w + 0.2, -1, 6, 0, h, wall)
    box("wall_back", -w, w, -1.2, -1, 0, h, wall)
    # The doorway at y=6 opens into a wider, daylit room.
    door_w, door_h = 0.45, 2.05
    box("door_wall_l", -3, -door_w, 6, 6.15, 0, h, wall)
    box("door_wall_r", door_w, 3, 6, 6.15, 0, h, wall)
    box("door_wall_t", -door_w, door_w, 6, 6.15, door_h, h, wall)
    box("frame_l", -door_w - 0.07, -door_w, 5.98, 6.17, 0, door_h + 0.07, trim)
    box("frame_r", door_w, door_w + 0.07, 5.98, 6.17, 0, door_h + 0.07, trim)
    box("frame_t", -door_w, door_w, 5.98, 6.17, door_h, door_h + 0.07, trim)
    box("door_leaf", door_w, door_w + 0.04, 6.17, 7.05, 0, door_h, flat("door", (0.62, 0.6, 0.55), 0.5))
    box("far_l", -3.2, -3, 6, length, 0, h, wall)
    box("far_r", 3, 3.2, 6, length, 0, h, wall)
    box("far_back", -3, 3, length, length + 0.2, 0, h, wall)
    box("skirt_l", -w, -w + 0.015, -1, 6, 0, 0.1, trim)
    box("skirt_r", w - 0.015, w, -1, 6, 0, 0.1, trim)
    place("hanging_picture_frame_02", -w + 0.015, 2.2, z=1.15, rot=90, scale=0.8)
    place("hanging_picture_frame_01", w - 0.015, 3.7, z=1.0, rot=-90, scale=0.7)
    place("ornate_mirror_01", -w + 0.015, 4.6, z=1.05, rot=90, scale=0.9)
    place("side_table_01", w - 0.25, 1.7, z=0, scale=0.7, rot=-90)
    place("potted_plant_04", w - 0.25, 1.7, drop=1.0)
    place("potted_plant_01", 1.6, 8.5, z=0)
    place("Sofa_01", -0.8, 10.3, z=0, rot=180)

    world = bpy.data.worlds.new("dark")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    bpy.context.scene.world = world
    for y in (0.5, 2.6, 4.7):
        bpy.ops.object.light_add(type="AREA", location=(0, y, h - 0.02))
        light = bpy.context.active_object
        light.data.size = 0.9
        light.data.energy = 26
        light.data.color = (1.0, 0.93, 0.82)
        light.visible_camera = False
    bpy.ops.object.light_add(type="AREA", location=(0, 8.5, h - 0.02))
    light = bpy.context.active_object
    light.data.size, light.data.shape, light.data.size_y = 4.0, "RECTANGLE", 4.0
    light.data.energy = 240
    light.data.color = (1.0, 0.97, 0.9)
    light.visible_camera = False

    cam = camera((0, 0.2, 1.6), (0, 8, 1.35), lens=24)
    start, end = 0.2, 8.0
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 72
    for frame in range(1, 73):
        t = (frame - 1) / 71
        eased = t * t * (3 - 2 * t)
        cam.location.y = start + (end - start) * eased
        cam.keyframe_insert("location", frame=frame)


# ---------------------------------------------------------------- render
def setup_render(width, height, samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.use_adaptive_sampling = True
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.3


def render_to(path, transparent=False, file_format="PNG", color_mode="RGB", quality=92):
    scene = bpy.context.scene
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = file_format
    scene.render.image_settings.color_mode = color_mode
    if file_format == "JPEG":
        scene.render.image_settings.quality = quality
    scene.render.filepath = str(path)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def render_final(room, samples):
    setup_render(OUT_W, OUT_H, samples)
    out = RAW / room
    scored = [r for r in placed if r["role"] == "scored"]
    if len(scored) != 15:
        raise SystemExit(f"{room}: expected 15 scored objects, found {len(scored)}")
    labels = [r["label"] for r in scored]
    if len(set(labels)) != len(labels):
        raise SystemExit(f"{room}: scored object labels must be unique")
    all_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    scene = bpy.context.scene

    def set_hidden(meshes, value):
        for mesh in meshes:
            mesh.hide_render = value

    if not (out / "full.png").exists():
        render_to(out / "full.png")
    set_hidden([m for r in scored for m in r["meshes"]], True)
    if not (out / "empty.png").exists():
        render_to(out / "empty.png")

    # Cutouts: the object alone, still lit and shadowed by the room it sits in.
    scene.cycles.samples = max(32, samples // 2)
    for index, record in enumerate(scored):
        target = out / "objects" / f"{index:02d}.png"
        mask = out / "masks" / f"{index:02d}.png"
        if target.exists() and mask.exists():
            continue
        mine = record["meshes"]
        others = [m for m in all_meshes if m not in mine]
        set_hidden(mine, False)
        for mesh in others:
            mesh.visible_camera = False
        render_to(target, transparent=True, color_mode="RGBA")
        # Mask: the same object with the rest of the room in front of it, to
        # measure how much of it the participant can really see.
        for mesh in others:
            mesh.visible_camera = True
            mesh.is_holdout = True
        keep_samples = scene.cycles.samples
        scene.cycles.samples = 8
        render_to(mask, transparent=True, color_mode="RGBA")
        scene.cycles.samples = keep_samples
        for mesh in others:
            mesh.is_holdout = False
        set_hidden(mine, True)
    (out / "objects.json").write_text(json.dumps(
        [{"index": i, "id": r["name"], "label": r["label"]} for i, r in enumerate(scored)], indent=2))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True, choices=["kitchen", "living_room", "hallway"])
    parser.add_argument("--mode", default="preview", choices=["preview", "final", "transition"])
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--frame", type=int, default=None, help="render one transition frame")
    args = parser.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    {"kitchen": build_kitchen, "living_room": build_living_room, "hallway": build_hallway}[args.scene]()

    if args.mode == "preview":
        setup_render(960, 540, 48)
        if args.frame:
            bpy.context.scene.frame_set(args.frame)
        suffix = f"_{args.frame:02d}" if args.frame else ""
        render_to(PREVIEW / f"{args.scene}{suffix}.png")
    elif args.mode == "final":
        render_final(args.scene, args.samples)
    else:
        setup_render(OUT_W, OUT_H, args.samples)
        scene = bpy.context.scene
        out = RAW / "transition"
        for frame in range(1, 73):
            target = out / f"{frame:02d}.jpg"
            if target.exists():
                continue
            scene.frame_set(frame)
            render_to(target, file_format="JPEG")


if __name__ == "__main__":
    main()
