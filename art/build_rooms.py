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
          role="clutter", label=None, lift=0.0, icon_rot=0.0, icon_rot_x=0.0, rot_y=0.0):
    """Import a model and stand it on the first surface under (x, y, drop).

    icon_rot and icon_rot_x set the object's pose in its tray icon, which is
    rendered separately in a neutral studio, never cut from the room."""
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
    root.rotation_euler = (math.radians(rot_x), math.radians(rot_y), math.radians(rot))
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
    record = {"name": name, "meshes": meshes, "role": role, "label": label or name,
              "icon": {"pick": pick, "rot": icon_rot, "rot_x": icon_rot_x}}
    placed.append(record)
    return record


def cylinder(name, x, y, z0, z1, radius, mat, rot_x=0.0, rot_y=0.0, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=z1 - z0,
                                        location=(x, y, (z0 + z1) / 2),
                                        rotation=(math.radians(rot_x), math.radians(rot_y), 0))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj


def hdri_world(name, rotation=0.0, strength=1.6):
    world = bpy.data.worlds.new(f"outdoors_{name}")
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(ROOT / "_downloads" / "hdri" / f"{name}.hdr"))
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0, 0, math.radians(rotation))
    links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    links.new(env.outputs["Color"], nodes["Background"].inputs["Color"])
    nodes["Background"].inputs["Strength"].default_value = strength
    bpy.context.scene.world = world


def socket(x, z, y=None, wall="back"):
    """Wall socket or switch plate: a small cream plate with two dark holes."""
    plate = flat("socket", (0.86, 0.85, 0.8), 0.35)
    dark = flat("socket_hole", (0.05, 0.05, 0.05), 0.6)
    half = ROOM_W / 2
    if wall == "back":
        box("socket", x - 0.045, x + 0.045, ROOM_BACK - 0.012, ROOM_BACK, z - 0.045, z + 0.045, plate)
        for dx in (-0.015, 0.015):
            box("socket_pin", x + dx - 0.004, x + dx + 0.004, ROOM_BACK - 0.013, ROOM_BACK - 0.011, z - 0.006, z + 0.006, dark)
    else:
        sign = -1 if wall == "left" else 1
        x0 = sign * half
        a, b = sorted((x0, x0 - sign * 0.012))
        box("socket", a, b, y - 0.045, y + 0.045, z - 0.045, z + 0.045, plate)
        a, b = sorted((x0 - sign * 0.011, x0 - sign * 0.013))
        for dy in (-0.015, 0.015):
            box("socket_pin", a, b, y + dy - 0.004, y + dy + 0.004, z - 0.006, z + 0.006, dark)


def curtain(name, x0, x1, z0, z1, y, mat, folds=7, depth=0.035):
    """Gathered curtain: a vertical sheet with sine folds."""
    import bmesh
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    cols, rows = folds * 8, 2
    grid = []
    for r in range(rows):
        row = []
        z = z0 + (z1 - z0) * r / (rows - 1)
        for c in range(cols + 1):
            t = c / cols
            x = x0 + (x1 - x0) * t
            yy = y - depth * (0.5 + 0.5 * math.sin(t * folds * 2 * math.pi))
            row.append(bm.verts.new((x, yy, z)))
        grid.append(row)
    for c in range(cols):
        bm.faces.new((grid[0][c], grid[0][c + 1], grid[1][c + 1], grid[1][c]))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    mod = obj.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = 0.008
    return obj


def shell(floor_mat, wall_mat, window=None, hdri="symmetrical_garden_02", hdri_rot=0.0,
          ceiling_light=40.0, sun=6.0, sun_rot=165.0, sill_depth=0.2):
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
        frame = flat("window_frame", (0.82, 0.81, 0.78), 0.4)
        f = 0.05
        for i, (a, b, c, d) in enumerate([
            (x0, x1, z0, z0 + f), (x0, x1, z1 - f, z1),
            (x0, x0 + f, z0 + f, z1 - f), (x1 - f, x1, z0 + f, z1 - f),
            ((x0 + x1) / 2 - f / 2, (x0 + x1) / 2 + f / 2, z0 + f, z1 - f),
            (x0 + f, x1 - f, z1 - 0.35, z1 - 0.35 + f * 0.8),
        ]):
            box(f"window_frame_{i}", a, b, ROOM_BACK + 0.08, ROOM_BACK + 0.14, c, d, frame)
        # Reveal: the wall thickness around the opening, so it reads as a real window.
        box("reveal_l", x0 - 0.001, x0, ROOM_BACK, ROOM_BACK + 0.08, z0, z1, wall_mat)
        box("reveal_r", x1, x1 + 0.001, ROOM_BACK, ROOM_BACK + 0.08, z0, z1, wall_mat)
        box("reveal_t", x0, x1, ROOM_BACK, ROOM_BACK + 0.08, z1, z1 + 0.001, wall_mat)
        glass = bpy.data.materials.new("glass")
        glass.use_nodes = True
        bsdf = glass.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Transmission Weight"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.0
        bsdf.inputs["IOR"].default_value = 1.05
        box("glass", x0 + f, x1 - f, ROOM_BACK + 0.105, ROOM_BACK + 0.11, z0 + f, z1 - f, glass)
        box("window_sill", x0 - 0.06, x1 + 0.06, ROOM_BACK - sill_depth + 0.08, ROOM_BACK + 0.1,
            z0 - 0.035, z0, frame)
    else:
        box("wall_b", -half, half, *back, 0, ROOM_H, wall_mat)

    hdri_world(hdri, hdri_rot)

    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(58), 0, math.radians(sun_rot)))
    bpy.context.active_object.data.energy = sun
    bpy.context.active_object.data.angle = math.radians(3)
    bpy.context.active_object.data.color = (1.0, 0.92, 0.8)

    # Soft fill from the ceiling, hidden from the camera. Weaker than before, so
    # the window and the visible lamp give the room a direction of light.
    for x in (-1.2, 1.2):
        bpy.ops.object.light_add(type="AREA", location=(x, -0.6, ROOM_H - 0.02))
        light = bpy.context.active_object
        light.data.shape = "RECTANGLE"
        light.data.size, light.data.size_y = 2.0, 2.6
        light.data.energy = ceiling_light
        light.data.color = (1.0, 0.94, 0.85)
        light.visible_camera = False
    # Bounce from behind the camera, standing in for the unseen front of the room.
    bpy.ops.object.light_add(type="AREA", location=(0, ROOM_FRONT + 0.1, 1.6),
                             rotation=(math.radians(90), 0, 0))
    light = bpy.context.active_object
    light.data.shape = "RECTANGLE"
    light.data.size, light.data.size_y = 3.5, 1.6
    light.data.energy = ceiling_light * 1.2
    light.data.color = (1.0, 0.95, 0.9)
    light.visible_camera = False


def pendant(x, y, bottom=1.78, energy=18.0, scale=1.0):
    """Visible hanging lamp with a warm bulb and a cord to the ceiling."""
    rec = place("modern_ceiling_lamp_01", x, y, z=bottom, scale=scale)
    low, high = world_bbox(rec["meshes"])
    if high.z < ROOM_H - 0.01:
        cylinder("lamp_cord", x, y, high.z, ROOM_H, 0.004, flat("cord", (0.05, 0.05, 0.05), 0.5))
    bpy.ops.object.light_add(type="POINT", location=(x, y, bottom + 0.08))
    light = bpy.context.active_object
    light.data.energy = energy
    light.data.shadow_soft_size = 0.05
    light.data.color = (1.0, 0.82, 0.6)
    return rec


def camera(location, target, lens=26):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.data.lens = lens
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


ROOM_CAMERA = ((0.0, -2.55, 1.55), (0.0, 1.0, 0.86), 26)


def base_cabinet(x0, x1, y0, y1, height, mat_body, mat_top, doors, top=True):
    box("cab_body", x0, x1, y0, y1, 0.09, height - 0.04, mat_body)
    box("cab_kick", x0, x1, y0 + 0.05, y1, 0, 0.09, flat("kick", (0.08, 0.08, 0.08), 0.6))
    if top:
        box("cab_top", x0 - 0.01, x1 + 0.01, y0 - 0.02, y1, height - 0.04, height, mat_top)
    width = (x1 - x0) / doors
    handle = flat("handle", (0.55, 0.55, 0.55), 0.3, 1.0)
    for i in range(doors):
        a, b = x0 + i * width + 0.006, x0 + (i + 1) * width - 0.006
        box(f"door_{i}", a, b, y0 - 0.018, y0, 0.11, height - 0.06, mat_body)
        mid = (a + b) / 2
        box(f"pull_{i}", mid - 0.06, mid + 0.06, y0 - 0.04, y0 - 0.02, height - 0.14, height - 0.128, handle)


def wall_shelf(name, x0, x1, z, depth, mat):
    """Open shelf on the back wall, with two brackets."""
    box(name, x0, x1, ROOM_BACK - depth, ROOM_BACK, z - 0.035, z, mat)
    metal = flat("bracket", (0.12, 0.12, 0.12), 0.4, 0.8)
    for bx in (x0 + 0.1, x1 - 0.1):
        box(f"{name}_bracket", bx - 0.012, bx + 0.012, ROOM_BACK - depth * 0.8, ROOM_BACK, z - 0.2, z - 0.035, metal)


def sink(x0, x1, y0, y1, counter_z, stone):
    """Counter top with a steel sink cut into it, and a tap."""
    steel = flat("sink_steel", (0.62, 0.62, 0.62), 0.25, 1.0)
    inner = flat("sink_inner", (0.42, 0.42, 0.43), 0.35, 1.0)
    sx0, sx1, sy0, sy1 = x0, x1, y0, y1
    depth = 0.2
    box("sink_rim_f", sx0 - 0.02, sx1 + 0.02, sy0 - 0.02, sy0, counter_z - 0.004, counter_z + 0.004, steel)
    box("sink_rim_b", sx0 - 0.02, sx1 + 0.02, sy1, sy1 + 0.06, counter_z - 0.004, counter_z + 0.004, steel)
    box("sink_rim_l", sx0 - 0.02, sx0, sy0, sy1, counter_z - 0.004, counter_z + 0.004, steel)
    box("sink_rim_r", sx1, sx1 + 0.02, sy0, sy1, counter_z - 0.004, counter_z + 0.004, steel)
    box("sink_floor", sx0, sx1, sy0, sy1, counter_z - depth - 0.01, counter_z - depth, inner)
    box("sink_wall_f", sx0, sx1, sy0, sy0 + 0.005, counter_z - depth, counter_z, inner)
    box("sink_wall_b", sx0, sx1, sy1 - 0.005, sy1, counter_z - depth, counter_z, inner)
    box("sink_wall_l", sx0, sx0 + 0.005, sy0, sy1, counter_z - depth, counter_z, inner)
    box("sink_wall_r", sx1 - 0.005, sx1, sy0, sy1, counter_z - depth, counter_z, inner)
    chrome = flat("chrome", (0.8, 0.8, 0.8), 0.12, 1.0)
    tx, ty = (sx0 + sx1) / 2, sy1 + 0.035
    cylinder("tap_base", tx, ty, counter_z, counter_z + 0.03, 0.028, chrome)
    cylinder("tap_column", tx, ty, counter_z + 0.03, counter_z + 0.3, 0.013, chrome)
    cylinder("tap_spout", tx, ty - 0.1, counter_z + 0.29, counter_z + 0.31, 0.011, chrome, verts=16)
    box("tap_arm", tx - 0.011, tx + 0.011, ty - 0.19, ty, counter_z + 0.287, counter_z + 0.31, chrome)
    cylinder("tap_nozzle", tx, ty - 0.18, counter_z + 0.25, counter_z + 0.29, 0.011, chrome)
    for dx in (-0.08, 0.08):
        cylinder("tap_handle", tx + dx, ty, counter_z, counter_z + 0.05, 0.018, chrome)


# ---------------------------------------------------------------- arrangements
# Round 3: each room type has one set of furniture and clutter, a pool of spots, and
# three arrangements. Arrangement k puts the same scored objects on different spots,
# so an object never stands where it stood in another condition. Every spot is a
# free patch of surface with clutter around it, and a spot not used in one
# arrangement is still a free patch, so an empty patch in the empty room is no clue.
ARRANGEMENT = 1
MODE = "preview"


def spot(x, y, drop=None, z=None, rot=0.0):
    return {"x": x, "y": y, "drop": drop, "z": z, "rot": rot}


def target(name, label, scale=1.0, pick=None, rot=0.0, rot_x=0.0, lift=0.0, icon_rot=0.0, icon_rot_x=0.0):
    return {"name": name, "label": label, "scale": scale, "pick": pick, "rot": rot, "rot_x": rot_x,
            "lift": lift, "icon_rot": icon_rot, "icon_rot_x": icon_rot_x}


def place_targets(objects, spots, arrangements):
    """Place each scored object on its spot for the current arrangement. In
    --mode spots, mark every spot in the pool instead, to choose arrangements."""
    if MODE == "spots":
        mark = flat("spot_marker", (1.0, 0.05, 0.4), 0.4, emit=2.0)
        for name, sp in spots.items():
            z = sp["z"] if sp["z"] is not None else surface_below(sp["x"], sp["y"], sp["drop"] or 2.5)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(sp["x"], sp["y"], z + 0.035))
            ball = bpy.context.active_object
            ball.data.materials.append(mark)
            placed.append({"name": name, "meshes": [ball], "role": "scored", "label": name, "icon": {}})
        return
    chosen = arrangements[ARRANGEMENT - 1]
    if len(set(chosen)) != len(chosen) or len(chosen) != len(objects):
        raise SystemExit("arrangement must use one distinct spot per object")
    for obj, spot_name in zip(objects, chosen):
        sp = spots[spot_name]
        place(obj["name"], sp["x"], sp["y"], z=sp["z"], drop=sp["drop"] or 2.5, rot=obj["rot"] + sp["rot"],
              rot_x=obj["rot_x"], scale=obj["scale"], pick=obj["pick"], role="scored", label=obj["label"],
              lift=obj["lift"], icon_rot=obj["icon_rot"], icon_rot_x=obj["icon_rot_x"])


# ---------------------------------------------------------------- rooms
def build_kitchen():
    shell(pbr("floor_terracotta", "patterned_terracotta_tiling", 0.9), paint("kitchen_wall", (0.76, 0.77, 0.68)),
          window=(0.15, 1.15, 1.08, 2.15), hdri="symmetrical_garden_02", hdri_rot=35, sun_rot=160)
    camera(*ROOM_CAMERA[:2], lens=ROOM_CAMERA[2])

    half = ROOM_W / 2
    front_y = ROOM_BACK - 0.62
    top_z = 0.92
    body = pbr("cabinet", "kitchen_wood", 1.0, tint=(0.83, 0.82, 0.76))
    stone = pbr("counter", "marble_01", 1.4, rough=0.22)
    # Counter run: fridge, prep, stove, sink under the window, then more counter.
    base_cabinet(-1.55, -1.0, front_y, ROOM_BACK, top_z, body, stone, 1)
    place("electric_stove", -0.75, ROOM_BACK - 0.33, z=0.06)
    box("stove_plinth", -1.0, -0.5, ROOM_BACK - 0.6, ROOM_BACK, 0, 0.06, flat("kick", (0.08, 0.08, 0.08), 0.6))
    base_cabinet(-0.5, half, front_y, ROOM_BACK, top_z, body, stone, 6, top=False)
    sx0, sx1, sy0, sy1 = 0.38, 0.92, front_y + 0.1, ROOM_BACK - 0.14
    box("top_a", -0.51, sx0 - 0.02, front_y - 0.02, ROOM_BACK, top_z - 0.04, top_z, stone)
    box("top_b", sx1 + 0.02, half, front_y - 0.02, ROOM_BACK, top_z - 0.04, top_z, stone)
    box("top_c", sx0 - 0.02, sx1 + 0.02, front_y - 0.02, sy0 - 0.02, top_z - 0.04, top_z, stone)
    box("top_d", sx0 - 0.02, sx1 + 0.02, sy1 + 0.06, ROOM_BACK, top_z - 0.04, top_z, stone)
    sink(sx0, sx1, sy0, sy1, top_z, stone)

    tile = pbr("splash", "long_white_tiles", 0.6, rough=0.15)
    box("splash_l", -1.55, 0.15, ROOM_BACK - 0.012, ROOM_BACK, top_z, 1.5, tile)
    box("splash_r", 1.15, half, ROOM_BACK - 0.012, ROOM_BACK, top_z, 1.5, tile)
    box("splash_u", 0.15, 1.15, ROOM_BACK - 0.012, ROOM_BACK, top_z, 1.045, tile)
    steel = flat("hood", (0.55, 0.55, 0.55), 0.3, 1.0)
    box("hood", -1.05, -0.45, ROOM_BACK - 0.48, ROOM_BACK, 1.68, 1.8, steel)
    box("hood_flue", -0.87, -0.63, ROOM_BACK - 0.3, ROOM_BACK, 1.8, ROOM_H, steel)

    # Wall cabinet over the prep counter, open shelves to the right of the window.
    upper = pbr("cabinet_up", "kitchen_wood", 1.0, tint=(0.83, 0.82, 0.76))
    box("upper_body", -1.55, -1.12, ROOM_BACK - 0.33, ROOM_BACK, 1.45, 2.15, upper)
    box("upper_door", -1.545, -1.125, ROOM_BACK - 0.348, ROOM_BACK - 0.33, 1.465, 2.135, upper)
    box("upper_pull", -1.18, -1.16, ROOM_BACK - 0.37, ROOM_BACK - 0.35, 1.5, 1.62, flat("handle", (0.55, 0.55, 0.55), 0.3, 1.0))
    plank = pbr("plank", "oak_veneer_01", 0.9)
    wall_shelf("shelf_r1", 1.4, 2.25, 1.42, 0.27, plank)
    wall_shelf("shelf_r2", 1.4, 2.25, 1.82, 0.27, plank)

    # Fridge in the back-left corner.
    white = flat("fridge", (0.86, 0.86, 0.84), 0.22)
    handle = flat("fridge_handle", (0.7, 0.7, 0.7), 0.25, 1.0)
    box("fridge", -2.28, -1.6, ROOM_BACK - 0.66, ROOM_BACK - 0.02, 0.02, 1.42, white)
    box("fridge_gap", -2.28, -1.6, ROOM_BACK - 0.672, ROOM_BACK - 0.66, 0.98, 0.99, flat("kick", (0.08, 0.08, 0.08), 0.6))
    box("fridge_h1", -1.7, -1.68, ROOM_BACK - 0.7, ROOM_BACK - 0.67, 1.06, 1.3, handle)
    box("fridge_h2", -1.7, -1.68, ROOM_BACK - 0.7, ROOM_BACK - 0.67, 0.62, 0.88, handle)
    box("fridge_note", -2.05, -1.88, ROOM_BACK - 0.664, ROOM_BACK - 0.66, 1.08, 1.28, flat("note", (0.93, 0.9, 0.78), 0.8))
    box("fridge_magnet", -1.99, -1.95, ROOM_BACK - 0.67, ROOM_BACK - 0.66, 1.26, 1.3, flat("magnet", (0.75, 0.12, 0.1), 0.4))
    box("fridge_photo", -2.2, -2.08, ROOM_BACK - 0.664, ROOM_BACK - 0.66, 0.6, 0.75, flat("photo", (0.35, 0.45, 0.55), 0.5))

    # Breakfast table and two chairs, a shelf unit on the left wall.
    place("wooden_table_02", 0.05, -0.35, z=0)
    place("painted_wooden_chair_01", -0.75, -0.35, z=0, rot=-90)
    place("painted_wooden_chair_01", 0.85, -0.35, z=0, rot=90)
    pendant(0.05, -0.35, bottom=1.9, scale=0.55)
    socket(-1.32, 1.12)
    socket(1.6, 1.12)
    socket(0, 0.3, y=-0.9, wall="left")
    socket(0, 1.15, y=-1.2, wall="right")

    # Scored: each a different kind of thing, each with more than one plausible spot.
    s = dict(role="scored")
    place("wooden_cutting_board", -1.33, ROOM_BACK - 0.4, drop=1.2, rot=5, label="cutting board",
          icon_rot_x=75, **s)
    place("brass_pan_01", -0.7, ROOM_BACK - 0.42, drop=1.2, rot=90, lift=0.012, label="brass pan", icon_rot=90,
          icon_rot_x=55, **s)
    place("multi_cleaner_bottle", -0.08, ROOM_BACK - 0.2, drop=1.2, rot=20, label="spray bottle", **s)
    place("vintage_electric_kettle", 1.12, ROOM_BACK - 0.32, drop=1.2, rot=-25, label="kettle", **s)
    place("wooden_stool_01", 1.9, 0.85, z=0)
    place("wicker_basket_01", 1.9, 0.85, drop=0.8, rot=10, label="wicker basket", **s)
    place("pot_enamel_01", 1.56, ROOM_BACK - 0.15, drop=1.6, label="enamel pot", **s)
    place("tea_set_01", 2.16, ROOM_BACK - 0.16, drop=1.6, pick=["cup_small_01"], scale=1.5, label="teacup", **s)
    place("carved_wooden_plate", 0.56, ROOM_BACK - 0.02, drop=1.3, rot_x=75, label="carved plate",
          icon_rot_x=75, **s)
    place("wine_bottles_01", -0.68, -0.35, drop=0.8, pick=["bordeaux"], label="wine bottle", **s)
    place("CheeseBox_01", -2.05, ROOM_BACK - 0.35, drop=1.6, rot=3, label="cheese box", **s)
    place("strawberry_chocolate_cake", -0.32, -0.42, drop=1.2, label="cake", **s)
    place("wooden_spoon", 0.02, -0.55, drop=1.2, rot=70, label="wooden spoon", icon_rot_x=75, **s)
    place("bananas", 0.4, -0.28, drop=1.2, pick=["bunch"], rot=-15, label="bananas", **s)
    place("plastic_thermos", 0.85, -0.35, drop=1.2, label="thermos", **s)
    place("wooden_bucket_01", -1.65, 0.8, z=0, pick=["bucket"], scale=0.75, rot=20, label="wooden bucket", **s)

    # Unscored clutter. Every surface that holds a scored object keeps other things too.
    place("hamburger_buns", -1.45, ROOM_BACK - 0.13, drop=1.2, scale=0.6)
    place("food_avocado_01", -1.08, ROOM_BACK - 0.35, drop=1.2)
    place("yellow_onion", -1.08, ROOM_BACK - 0.2, drop=1.2)
    place("long_life_food", 0.2, ROOM_BACK - 0.12, drop=1.2, pick=["tomatoes"])
    place("all_purpose_cleaner", 0.98, ROOM_BACK - 0.12, drop=1.2, scale=0.8)
    place("bleach_bottle", 0.12, ROOM_BACK - 0.45, drop=1.2, scale=0.85)
    place("wooden_bowl_02", 1.62, ROOM_BACK - 0.45, drop=1.2, scale=0.8)
    place("food_lime_01", 1.6, ROOM_BACK - 0.45, drop=1.25)
    place("lemon", 1.68, ROOM_BACK - 0.4, drop=1.25)
    place("plastic_bottle_gallon", 2.1, ROOM_BACK - 0.14, drop=1.2, scale=0.45)
    place("wine_bottles_01", 1.85, ROOM_BACK - 0.14, drop=1.2, pick=["alsace"], scale=0.9)
    place("russian_food_cans_01", 1.95, ROOM_BACK - 0.5, drop=1.2)
    place("ceramic_pot", 2.1, ROOM_BACK - 0.14, drop=2.0, scale=0.55)
    place("metal_jug", 1.62, ROOM_BACK - 0.14, drop=2.0, scale=0.5)
    place("brass_pot_02", 1.85, ROOM_BACK - 0.14, drop=2.0, scale=0.5)
    place("planter_pot_clay", 0.33, ROOM_BACK + 0.02, drop=1.2, scale=0.35)
    place("potted_plant_02", 0.97, ROOM_BACK + 0.02, drop=1.2, scale=0.32)
    place("long_life_food", -1.75, ROOM_BACK - 0.3, drop=1.6, pick=["milk"])
    place("cardboard_box_01", -1.6, ROOM_BACK - 0.2, drop=2.4, scale=0.4)
    place("brass_pot_01", -1.32, ROOM_BACK - 0.17, drop=2.4, scale=0.55)
    place("wooden_crate_01", 1.52, 0.9, z=0, rot=-80, scale=0.55, pick=["wooden_crate_01"])
    place("sweet_potato", 1.5, 0.95, drop=0.8)
    place("food_pomegranate_01", 1.58, 0.82, drop=0.8)
    place("tea_set_01", -0.08, -0.13, drop=1.2, pick=["plate_large_circular_03"])
    place("croissant", -0.08, -0.13, drop=1.2, rot=30)
    place("food_pears_asian_01", 0.62, -0.18, drop=1.2, pick=["_a"])
    place("wooden_candlestick", 0.18, -0.08, drop=1.2, scale=0.6)
    place("office_notepads", -0.55, -0.15, drop=1.2, pick=["yellow_pad"], scale=0.7, rot=-12)
    place("hanging_picture_frame_03", half - 0.015, -0.1, z=1.45, rot=-90, scale=0.6)
    place("plastic_broom", -half + 0.12, 0.9, z=0, rot=90, scale=0.85)


LIVING_OBJECTS = [
    target("chess_set", "chess set", scale=0.4, rot=10),
    target("horse_statue_01", "horse statue", rot=60),
    target("Ukulele_01", "ukulele", rot_x=90, rot=40, lift=0.02),
    target("boombox", "boombox", scale=0.45),
    target("concrete_cat_statue", "cat statue", scale=0.7, rot=-25, icon_rot=-25),
    target("wicker_basket_01", "wicker basket", scale=0.8, rot=15),
]


def build_living_room():
    shell(pbr("floor_parquet", "herringbone_parquet", 1.4), paint("living_wall", (0.62, 0.68, 0.72)),
          window=(-0.3, 1.0, 1.0, 2.2), hdri="cloudy_vondelpark", hdri_rot=-40, sun=4.0, sun_rot=195,
          sill_depth=0.24)
    camera(*ROOM_CAMERA[:2], lens=ROOM_CAMERA[2])

    half = ROOM_W / 2
    cloth = flat("curtain", (0.74, 0.71, 0.63), 0.95)
    curtain("curtain_l", -0.75, -0.25, 0.25, 2.42, ROOM_BACK - 0.06, cloth)
    curtain("curtain_r", 0.95, 1.45, 0.25, 2.42, ROOM_BACK - 0.06, cloth)
    cylinder("curtain_rod", -0.8, ROOM_BACK - 0.07, 0, 2.3, 0.012, flat("rod", (0.2, 0.18, 0.15), 0.4, 0.8),
             rot_y=90)
    bpy.context.active_object.location = (0.35, ROOM_BACK - 0.07, 2.45)

    rug = pbr("rug", "poly_wool_herringbone", 0.35, tint=(0.72, 0.6, 0.5), rough=0.95)
    box("rug", -1.2, 1.2, -0.9, 1.2, 0, 0.018, rug)

    # Sofa with its back to us, facing a TV on the back wall.
    place("wooden_bookshelf_worn", -1.6, ROOM_BACK - 0.3, z=0)
    place("small_wooden_table_01", 1.55, ROOM_BACK - 0.25, z=0)
    tv_z = surface_below(1.55, ROOM_BACK - 0.25, 1.5)
    black = flat("tv_black", (0.02, 0.02, 0.02), 0.25)
    box("tv_foot", 1.4, 1.7, ROOM_BACK - 0.33, ROOM_BACK - 0.17, tv_z, tv_z + 0.015, black)
    box("tv_neck", 1.53, 1.57, ROOM_BACK - 0.24, ROOM_BACK - 0.21, tv_z, tv_z + 0.08, black)
    box("tv_panel", 1.18, 1.92, ROOM_BACK - 0.25, ROOM_BACK - 0.21, tv_z + 0.07, tv_z + 0.5, black)
    box("tv_screen", 1.195, 1.905, ROOM_BACK - 0.252, ROOM_BACK - 0.25, tv_z + 0.085, tv_z + 0.485,
        flat("tv_screen", (0.01, 0.012, 0.015), 0.05))
    place("sofa_02", 0.0, -0.45, z=0.018, rot=180)
    place("modern_coffee_table_01", 0.0, 0.55, z=0.018, rot=90)
    place("Ottoman_01", 1.35, 0.25, z=0.018, scale=0.7, rot=15)
    place("side_table_01", -2.02, 0.85, z=0, rot=90)
    plank = pbr("plank", "oak_veneer_01", 0.9)
    box("wall_shelf", half - 0.2, half, 0.75, 1.45, 1.21, 1.24, plank)
    metal = flat("bracket", (0.12, 0.12, 0.12), 0.4, 0.8)
    for by in (0.85, 1.35):
        box("wall_shelf_bracket", half - 0.16, half, by - 0.012, by + 0.012, 1.05, 1.21, metal)
    pendant(0.0, 0.55, bottom=1.98, energy=14, scale=0.55)
    socket(1.0, 0.3)
    socket(half, 0.3, y=1.3, wall="right")

    # Bookshelf shelves sit at z 0.11, 0.39, 0.67, 0.96, 1.28, 1.66 and 2.06; only those
    # below eye height (1.55 m) hold scored objects, so no shelf lip hides them.
    s = {
        "book_1": spot(-1.25, ROOM_BACK - 0.3, drop=0.6),
        "book_2l": spot(-1.95, ROOM_BACK - 0.3, drop=0.9),
        "book_3": spot(-1.3, ROOM_BACK - 0.3, drop=1.2),
        "book_4l": spot(-2.0, ROOM_BACK - 0.3, drop=1.5),
        "book_4r": spot(-1.2, ROOM_BACK - 0.3, drop=1.5),
        "sill": spot(0.05, ROOM_BACK - 0.06, drop=1.2),
        "sill_r": spot(0.75, ROOM_BACK - 0.06, drop=1.2),
        "tv_l": spot(1.25, ROOM_BACK - 0.35, drop=0.8),
        "tv_r": spot(1.92, ROOM_BACK - 0.3, drop=0.8),
        "coffee_l": spot(-0.45, 0.45, drop=0.6),
        "coffee_r": spot(0.52, 0.62, drop=0.6),
        "ottoman": spot(1.3, 0.2, drop=0.8),
        "side_top": spot(-2.02, 0.75, drop=0.8),
        "wall_shelf": spot(ROOM_W / 2 - 0.1, 1.15, drop=1.5, rot=90),
        "book_0": spot(-1.3, ROOM_BACK - 0.3, drop=0.3),
        "coffee_m": spot(0.0, 0.78, drop=0.6),
        "wall_shelf_2": spot(ROOM_W / 2 - 0.1, 0.85, drop=1.5),
    }
    arrangements = [
        ["coffee_l", "book_4r", "coffee_r", "book_1", "tv_l", "ottoman"],
        ["tv_r", "side_top", "book_0", "wall_shelf", "coffee_r", "book_2l"],
        ["book_3", "sill_r", "coffee_m", "sill", "wall_shelf_2", "book_4l"],
    ]
    place_targets(LIVING_OBJECTS, s, arrangements)

    # Unscored clutter, denser than round 2.
    place("book_encyclopedia_set_01", -1.62, ROOM_BACK - 0.28, drop=0.9, scale=0.7, pick=["book01", "book02", "book03", "book04"])
    place("book_encyclopedia_set_01", -1.75, ROOM_BACK - 0.28, drop=0.3, scale=0.65, pick=["book01", "book02", "book03"])
    place("office_notepads", -1.55, ROOM_BACK - 0.3, drop=1.2, pick=["a4_stack"], scale=0.8)
    place("mantel_clock_01", -1.6, ROOM_BACK - 0.3, drop=1.5, scale=0.9)
    place("book_encyclopedia_set_01", -1.55, ROOM_BACK - 0.28, drop=1.9, scale=0.8)
    place("postcard_set_01", -1.65, ROOM_BACK - 0.35, drop=0.6, scale=0.55)
    place("lambis_shell", -2.1, ROOM_BACK - 0.35, drop=0.6, scale=1.4, rot=200)
    place("filmstrip_projector_8mm", -2.0, ROOM_BACK - 0.3, drop=1.2, rot=90, scale=0.6)
    place("brass_goblets", -1.65, ROOM_BACK - 0.3, drop=1.2, scale=0.4)
    place("calathea_orbifolia_01", 0.42, ROOM_BACK - 0.06, drop=1.2, scale=0.25)
    place("potted_plant_04", -0.3, ROOM_BACK - 0.05, drop=1.2, scale=1.0)
    place("throw_pillows_01", 0.55, -0.32, drop=1.0, pick=["pillow01"], rot=-10, scale=0.6)
    place("throw_pillows_01", -0.55, -0.32, drop=1.0, pick=["pillow02"], rot=10, scale=0.6)
    place("office_notepads", -0.05, 0.74, drop=0.6, pick=["yellow_pad"], scale=0.8, rot=15)
    place("tea_set_01", 0.05, 0.42, drop=0.6, pick=["saucer_circular_04"])
    place("tea_set_01", 0.05, 0.42, drop=0.6, pick=["cup_small_02"])
    place("round_spectacles", -0.15, 0.62, drop=0.65, rot=-20)
    place("book_encyclopedia_set_01", 0.15, 0.75, drop=0.6, rot_x=90, rot=80, scale=0.45, pick=["book05"])
    place("binder_notebook", -2.05, 0.7, drop=0.8, scale=0.4, rot=10)
    place("brass_candleholders", 1.6, ROOM_BACK - 0.33, drop=0.8, pick=["candleholder_02"], scale=0.5)
    place("office_notepads", 1.62, ROOM_BACK - 0.12, drop=0.8, pick=["a4_stack"], rot=0, scale=0.5)
    place("standing_picture_frame_02", -2.05, 0.95, drop=0.8, rot=60, scale=0.8)
    place("book_encyclopedia_set_01", -2.02, 1.05, drop=0.4, rot=90, scale=0.4, pick=["book03", "book04"])
    place("fancy_picture_frame_01", 1.55, ROOM_BACK - 0.015, z=1.45, scale=0.6)
    place("hanging_picture_frame_01", -0.6, ROOM_BACK - 0.015, z=1.75, scale=0.45)
    place("potted_plant_01", -0.72, ROOM_BACK - 0.35, z=0, scale=0.75)
    place("antique_ceramic_vase_01", 2.05, 0.45, z=0, scale=0.85)
    place("cardboard_box_01", 0.95, ROOM_BACK - 0.25, z=0.018, scale=0.35, rot=-15)
    place("ceramic_vase_03", -2.05, ROOM_BACK - 0.3, drop=0.3, scale=0.6)
    place("book_encyclopedia_set_01", 1.2, 0.12, drop=0.8, rot_x=90, rot=-30, scale=0.4, pick=["book06"])
    place("brass_vase_03", -0.05, ROOM_BACK - 0.06, drop=1.2, scale=1.2)
    place("hanging_picture_frame_02", 2.3 - 0.015, 0.6, z=1.6, rot=-90, scale=0.45)


def build_hallway():
    """Entry hall for the practice room. Its 5 objects share no kind with the test rooms."""
    shell(pbr("floor_laminate", "laminate_floor_02", 1.4), paint("hall_wall", (0.8, 0.77, 0.7)),
          window=None, ceiling_light=55.0, sun=0.0)
    camera(*ROOM_CAMERA[:2], lens=ROOM_CAMERA[2])
    half = ROOM_W / 2
    trim = flat("trim", (0.8, 0.79, 0.75), 0.45)
    # Front door in the back wall, with a glass light above it.
    door = flat("front_door", (0.25, 0.32, 0.36), 0.45)
    box("door_frame_l", -0.75, -0.68, ROOM_BACK - 0.03, ROOM_BACK, 0, 2.08, trim)
    box("door_frame_r", 0.28, 0.35, ROOM_BACK - 0.03, ROOM_BACK, 0, 2.08, trim)
    box("door_frame_t", -0.75, 0.35, ROOM_BACK - 0.03, ROOM_BACK, 2.08, 2.15, trim)
    box("door_leaf", -0.68, 0.28, ROOM_BACK - 0.02, ROOM_BACK, 0, 2.08, door)
    for i, (z0, z1) in enumerate([(0.2, 0.95), (1.1, 1.9)]):
        box(f"door_panel_{i}", -0.58, 0.18, ROOM_BACK - 0.03, ROOM_BACK - 0.02, z0, z1, door)
    brass = flat("brass", (0.75, 0.58, 0.3), 0.3, 1.0)
    box("door_handle", 0.12, 0.2, ROOM_BACK - 0.07, ROOM_BACK - 0.03, 1.0, 1.02, brass)
    box("door_mat", -0.62, 0.22, ROOM_BACK - 0.68, ROOM_BACK - 0.12, 0, 0.012,
        flat("door_mat", (0.12, 0.11, 0.1), 1.0))
    runner = pbr("runner", "poly_wool_herringbone", 0.3, tint=(0.5, 0.42, 0.36), rough=0.95)
    box("runner", -0.75, 0.35, -1.6, ROOM_BACK - 0.85, 0, 0.012, runner)
    # Coat rail with hooks and a bench on the left, shoe rack and console on the right.
    wood = pbr("rail", "oak_veneer_01", 0.8)
    box("coat_rail", -2.05, -1.05, ROOM_BACK - 0.025, ROOM_BACK, 1.62, 1.72, wood)
    for hx in (-1.9, -1.65, -1.4, -1.15):
        box("hook", hx - 0.01, hx + 0.01, ROOM_BACK - 0.09, ROOM_BACK - 0.025, 1.62, 1.66, brass)
    place("painted_wooden_bench", -1.55, ROOM_BACK - 0.28, z=0)
    rack = pbr("rack", "oak_veneer_01", 0.8, tint=(0.75, 0.7, 0.62))
    x0, x1, depth = 0.6, 1.35, 0.32
    for x in (x0, x1 - 0.02):
        box("rack_side", x, x + 0.02, ROOM_BACK - depth, ROOM_BACK, 0, 0.52, rack)
    for z in (0.06, 0.29, 0.52):
        box("rack_shelf", x0, x1, ROOM_BACK - depth, ROOM_BACK, z - 0.02, z, rack)
    place("side_table_tall_01", 1.75, ROOM_BACK - 0.22, z=0)
    place("ornate_mirror_01", 1.75, ROOM_BACK - 0.015, z=1.1)
    place("potted_plant_01", 2.1, 0.9, z=0, scale=0.8)
    pendant(-0.2, 0.3, bottom=2.0, energy=16, scale=0.5)
    socket(-0.95, 0.3)
    socket(0.45, 1.15)
    socket(0, 1.1, y=1.2, wall="right")

    objects = [
        target("fishermans_hat", "hat", rot=20),
        target("vintage_flashlight", "flashlight", rot=80),
        target("rubber_boots", "boots", pick=["boots_l", "boots_r"]),
        target("garden_gloves_01", "gloves", rot=40),
        target("vintage_suitcase", "suitcase", pick=["suitcase_01"], rot=-15),
    ]
    s = {
        "bench_l": spot(-1.85, ROOM_BACK - 0.28, drop=1.0),
        "bench_r": spot(-1.25, ROOM_BACK - 0.28, drop=1.0),
        "rack_top_l": spot(0.8, ROOM_BACK - 0.16, drop=0.8),
        "rack_top_r": spot(1.12, ROOM_BACK - 0.16, drop=0.8),
        "rack_mid": spot(0.95, ROOM_BACK - 0.16, drop=0.4),
        "console": spot(1.75, ROOM_BACK - 0.22, drop=1.0),
        "floor_bench": spot(-1.75, 0.75, z=0),
        "floor_right": spot(1.55, 0.65, z=0),
        "floor_left": spot(-0.95, 0.55, z=0.012),
        "mat": spot(-0.2, ROOM_BACK - 0.4, z=0.012),
    }
    arrangements = [
        ["bench_l", "bench_r", "rack_top_r", "console", "floor_bench"],
        ["console", "rack_mid", "floor_left", "bench_l", "floor_right"],
        ["rack_top_l", "floor_right", "mat", "bench_r", "bench_l"],
    ]
    place_targets(objects, s, arrangements)

    place("wicker_basket_02", -1.25, ROOM_BACK - 0.3, z=0, scale=0.65)
    place("cardboard_box_01", 0.8, ROOM_BACK - 0.17, drop=0.8, scale=0.4, rot=90)
    place("planter_pot_clay", 1.8, ROOM_BACK - 0.15, drop=1.0, scale=0.3)
    place("postcard_set_01", -1.5, ROOM_BACK - 0.28, drop=1.0, scale=0.7, rot=10)
    place("book_encyclopedia_set_01", 0.97, ROOM_BACK - 0.16, drop=0.4, scale=0.7, pick=["book01", "book02", "book03"])
    place("hanging_picture_frame_03", 1.0, ROOM_BACK - 0.015, z=1.4, scale=0.6)
    place("fancy_picture_frame_01", -1.55, ROOM_BACK - 0.015, z=1.95, scale=0.45)


BEDROOM_OBJECTS = [
    target("binoculars", "binoculars", scale=1.4, rot=10),
    target("vintage_video_camera", "video camera", scale=1.5, rot=-60, icon_rot=-60),
    target("Lantern_01", "lantern", scale=0.9),
    target("rubber_duck_toy", "rubber duck", scale=0.55, rot=-30, icon_rot=-30),
    target("carved_wooden_elephant", "wooden elephant", scale=1.8, rot=-30, icon_rot=-30),
    target("brass_vase_02", "brass vase", scale=0.55),
]


def build_bedroom():
    shell(pbr("floor_wood", "wood_floor", 1.6), paint("bed_wall", (0.72, 0.66, 0.6)),
          window=(0.15, 1.0, 1.0, 2.2), hdri="cloudy_vondelpark", hdri_rot=60, sun=4.5, sun_rot=200,
          sill_depth=0.24)
    camera(*ROOM_CAMERA[:2], lens=ROOM_CAMERA[2])
    half = ROOM_W / 2
    blind = flat("blind", (0.85, 0.82, 0.74), 0.9)
    box("blind", 0.17, 0.98, ROOM_BACK - 0.03, ROOM_BACK, 1.85, 2.18, blind)
    rug = pbr("bed_rug", "wool_boucle", 0.5, tint=(0.75, 0.68, 0.6), rough=0.95)
    box("rug", -0.75, 1.15, -0.6, 1.1, 0, 0.015, rug)

    # Bed with its head on the back wall, on the left, made up with a blanket.
    place("old_bed_frame", -1.75, ROOM_BACK - 1.02, z=0, scale=(1.4, 1.0, 1.0))
    top = surface_below(-1.75, 0.6, 1.0)
    blanket = pbr("blanket", "wool_boucle", 0.3, tint=(0.45, 0.55, 0.62), rough=0.95)
    sheet = flat("sheet", (0.88, 0.86, 0.82), 0.9)
    box("mattress", -2.36 + 0.07, -1.14 - 0.07, ROOM_BACK - 1.95, ROOM_BACK - 0.08, top, top + 0.16, sheet)
    box("blanket", -2.3, -1.12, ROOM_BACK - 1.98, ROOM_BACK - 0.6, top + 0.16, top + 0.2, blanket)
    box("blanket_side", -1.14, -1.12, ROOM_BACK - 1.98, ROOM_BACK - 0.6, top - 0.1, top + 0.2, blanket)
    box("blanket_fold", -2.3, -1.12, ROOM_BACK - 0.75, ROOM_BACK - 0.55, top + 0.2, top + 0.24, sheet)
    place("throw_pillows_01", -1.75, ROOM_BACK - 0.3, drop=1.2, pick=["pillow01"], scale=0.85)
    place("throw_pillows_01", -1.45, ROOM_BACK - 0.45, drop=1.2, pick=["pillow02"], scale=0.6, rot=15)
    place("painted_wooden_nightstand", -0.5, ROOM_BACK - 0.28, z=0)
    # Desk under the window; armchair in the front right corner.
    place("SchoolDesk_01", 0.58, ROOM_BACK - 0.3, z=0, rot=180)
    place("GreenChair_01", 1.6, 0.05, z=0.015, rot=35)
    # Chest of drawers on the back wall, right; a wall shelf above the armchair.
    place("GothicCommode_01", 1.68, ROOM_BACK - 0.3, z=0)
    plank = pbr("plank", "oak_veneer_01", 0.9)
    wall_shelf("wall_shelf", -0.95, -0.05, 1.32, 0.22, plank)
    place("painted_wooden_stool", 0.1, -0.15, z=0.015)
    footstool = place("Ottoman_01", 1.05, -0.15, z=0.015, rot=20, scale=0.45)
    footstool_top = world_bbox(footstool["meshes"])[1].z
    place("wicker_basket_02", -0.2, 1.15, z=0.015, pick=["wicker_basket_02_base"], scale=1.0, rot=20)
    pendant(-0.2, 0.2, bottom=2.0, energy=14, scale=0.5)
    place("fancy_picture_frame_01", -1.55, ROOM_BACK - 0.015, z=1.75, scale=0.55)
    place("hanging_picture_frame_03", 1.68, ROOM_BACK - 0.015, z=1.6, scale=0.6)
    place("ornate_mirror_01", half - 0.015, 1.35, z=1.35, rot=-90, scale=0.6)
    socket(-0.85, 0.3)
    socket(1.0, 0.3)

    s = {
        "night": spot(-0.52, ROOM_BACK - 0.33, drop=1.2),
        "desk_l": spot(0.3, ROOM_BACK - 0.3, drop=1.2),
        "desk_r": spot(0.82, ROOM_BACK - 0.3, drop=1.2),
        "chest_l": spot(1.25, ROOM_BACK - 0.33, drop=1.6),
        "chest_r": spot(2.08, ROOM_BACK - 0.33, drop=1.6),
        "chest_m": spot(1.62, ROOM_BACK - 0.4, drop=1.6),
        "sill": spot(0.58, ROOM_BACK - 0.06, drop=1.3),
        "stool": spot(0.1, -0.15, drop=0.8),
        "fold_stool": spot(1.05, -0.15, z=footstool_top),
        "shelf_l": spot(-0.82, ROOM_BACK - 0.11, drop=1.5),
        "shelf_r": spot(-0.25, ROOM_BACK - 0.11, drop=1.5),
        "floor_desk": spot(1.0, 1.2, z=0.015),
        "floor_chest": spot(1.3, 1.05, z=0.015),
        "rug_front": spot(0.6, 0.0, z=0.015),
        "rug_back": spot(0.75, 0.75, z=0.015),
        "bed_foot": spot(-1.45, 0.55, drop=1.2),
        "bed_side": spot(-2.0, 0.7, drop=1.2),
        "floor_night": spot(-0.6, 1.05, z=0.015),
    }
    arrangements = [
        ["night", "chest_r", "rug_front", "shelf_l", "desk_r", "floor_chest"],
        ["desk_l", "bed_side", "chest_l", "floor_desk", "stool", "shelf_r"],
        ["chest_m", "fold_stool", "sill", "bed_foot", "rug_back", "floor_night"],
    ]
    place_targets(BEDROOM_OBJECTS, s, arrangements)

    # Clutter around every spot.
    place("alarm_clock_01", -0.36, ROOM_BACK - 0.18, drop=1.2, rot=-20, scale=0.9)
    place("book_encyclopedia_set_01", -0.68, ROOM_BACK - 0.2, drop=1.2, pick=["book01", "book02"], scale=0.45, rot=90)
    place("desk_lamp_arm_01", 0.98, ROOM_BACK - 0.12, drop=1.2, rot=200, scale=0.7)
    place("office_notepads", 0.56, ROOM_BACK - 0.42, drop=1.2, pick=["a4_stack"], scale=0.6, rot=8)
    place("ceramic_vase_04", 1.44, ROOM_BACK - 0.18, drop=1.6, scale=0.8)
    place("standing_picture_frame_01", 1.85, ROOM_BACK - 0.15, drop=1.6, rot=-80)
    place("wooden_bowl_02", 1.86, ROOM_BACK - 0.45, drop=1.6, scale=0.45)
    place("round_spectacles", 1.25, ROOM_BACK - 0.5, drop=1.6, rot=15)
    place("postcard_set_01", 0.32, ROOM_BACK - 0.06, drop=1.3, scale=0.5)
    place("potted_plant_04", 0.86, ROOM_BACK - 0.07, drop=1.3, scale=0.8)
    place("book_encyclopedia_set_01", -0.55, ROOM_BACK - 0.1, drop=1.5, pick=["book01", "book02", "book03"], scale=0.45)
    place("wooden_candlestick", -0.06, ROOM_BACK - 0.1, drop=1.5, scale=0.6)
    place("binder_notebook", -1.7, 0.75, drop=1.2, scale=0.5, rot=80)
    place("cardboard_box_01", 2.0, 1.15, z=0, scale=0.45, rot=10)
    place("book_encyclopedia_set_01", 1.6, 1.12, z=0.015, scale=0.5, rot_x=90, pick=["book04", "book05", "book06"])
    place("potted_plant_01", -0.95, 0.85, z=0, scale=0.45)
    place("tea_set_01", 0.22, -0.05, drop=0.8, pick=["cup_small_02"])
    place("cardboard_box_01", 0.45, 0.5, z=0.015, scale=0.35, rot=30)
    place("hanging_picture_frame_01", -0.5, ROOM_BACK - 0.015, z=1.75, scale=0.5)
    place("hanging_picture_frame_02", -2.3 + 0.015, 1.4, z=1.55, rot=90, scale=0.5)
    place("cardboard_box_01", 0.75, ROOM_BACK - 0.3, z=0, scale=0.35, rot=-5)
    place("book_encyclopedia_set_01", 0.32, ROOM_BACK - 0.3, z=0.0, scale=0.55, rot_x=90, rot=90, pick=["book02", "book03", "book04"])
    place("potted_plant_02", 2.05, 1.05, z=0.015, scale=0.6)
    place("office_notepads", 0.62, ROOM_BACK - 0.2, drop=1.2, pick=["yellow_pad"], scale=0.5, rot=-12)
    place("brass_goblets", 2.0, ROOM_BACK - 0.2, drop=1.6, scale=0.35)


GARAGE_OBJECTS = [
    target("american_football", "football", scale=0.6, rot=20, icon_rot=20),
    target("watering_can_metal_01", "watering can", scale=0.8, rot=70, icon_rot=70),
    target("garden_gnome", "garden gnome", scale=0.55, rot=-15),
    target("tire_pump", "tire pump", scale=0.8, rot=10),
    target("metal_toolbox", "toolbox", scale=0.75, rot=-8),
    target("Megaphone_01", "megaphone", scale=0.7, rot=-60, icon_rot=-60),
]


def build_garage():
    shell(pbr("garage_floor", "garage_floor", 2.0), paint("garage_wall", (0.62, 0.63, 0.6)),
          window=(0.55, 1.35, 1.35, 2.15), hdri="symmetrical_garden_02", hdri_rot=-70, sun=3.0, sun_rot=150,
          ceiling_light=55.0, sill_depth=0.16)
    camera(*ROOM_CAMERA[:2], lens=ROOM_CAMERA[2])
    half = ROOM_W / 2
    bpy.ops.object.light_add(type="AREA", location=(0.0, 0.4, ROOM_H - 0.05))
    tube = bpy.context.active_object
    tube.data.shape, tube.data.size, tube.data.size_y = "RECTANGLE", 1.2, 0.12
    tube.data.energy = 120
    tube.data.color = (0.95, 0.97, 1.0)
    box("tube_housing", -0.62, 0.62, 0.32, 0.48, ROOM_H - 0.06, ROOM_H, flat("tube", (0.92, 0.93, 0.95), 0.3, emit=3.0))

    # Back wall: tall steel shelves on the left, a workbench with a pegboard in the
    # middle, a metal rack on the right. Tool cart, tool chest, crates and a barrel
    # in front.
    place("steel_frame_shelves_02", -2.0, ROOM_BACK - 0.27, z=0)
    place("steel_frame_shelves_02", -1.42, ROOM_BACK - 0.27, z=0)
    place("WoodenTable_03", -0.15, ROOM_BACK - 0.3, z=0)
    board = flat("pegboard", (0.62, 0.5, 0.36), 0.8)
    box("pegboard", -0.8, 0.5, ROOM_BACK - 0.02, ROOM_BACK, 1.0, 1.75, board)
    place("handsaw_wood", -0.55, ROOM_BACK - 0.03, z=1.25, rot=90, rot_x=0)
    place("wooden_hammer_01", -0.2, ROOM_BACK - 0.03, z=1.35, rot=0)
    place("measuring_tape_01", 0.1, ROOM_BACK - 0.05, z=1.45, rot=90)
    place("worn_metal_rack", 1.85, ROOM_BACK - 0.32, z=0)
    place("metal_jerrycan", -1.35, 0.2, z=0, rot=40)
    place("wooden_crate_02", 0.95, 0.45, z=0, rot=80)
    place("old_tyre", 0.2, ROOM_BACK - 0.75, z=0, rot_x=90, rot=-10)
    place("plastic_crate_03", 0.45, 1.05, z=0, rot=15)
    place("plastic_crate_02", 1.35, ROOM_BACK - 0.32, z=0, rot=5)
    place("plastic_crate_02", 1.35, ROOM_BACK - 0.32, drop=0.8, rot=-3)
    place("Barrel_02", 2.0, 0.55, z=0)
    place("plastic_monobloc_chair_01", 1.8, -0.2, z=0, rot=200)
    place("garden_hose_wall_mounted_01", half - 0.02, 0.9, z=1.0, rot=-90)
    socket(0.65, 1.0)
    socket(-0.95, 0.3)

    s = {
        "bench_l": spot(-0.6, ROOM_BACK - 0.35, drop=1.2),
        "bench_r": spot(0.3, ROOM_BACK - 0.35, drop=1.2),
        "shelf_l_low": spot(-2.0, ROOM_BACK - 0.27, drop=0.5),
        "shelf_l_mid": spot(-2.0, ROOM_BACK - 0.27, drop=0.9),
        "shelf_l_top": spot(-2.0, ROOM_BACK - 0.27, drop=1.4),
        "shelf_r_low": spot(-1.42, ROOM_BACK - 0.27, drop=0.5),
        "shelf_r_top": spot(-1.42, ROOM_BACK - 0.27, drop=1.4),
        "sill": spot(0.95, ROOM_BACK - 0.05, drop=1.6),
        "rack_low": spot(1.85, ROOM_BACK - 0.32, drop=0.6),
        "rack_mid": spot(1.85, ROOM_BACK - 0.32, drop=1.1),
        "chest_l": spot(0.62, 0.45, drop=1.0),
        "chest_r": spot(1.28, 0.45, drop=1.0),
        "floor_center": spot(0.1, 0.3, z=0),
        "barrel": spot(2.0, 0.55, drop=1.2),
        "floor_bench": spot(-0.4, 1.05, z=0),
        "floor_mid": spot(-0.45, 0.6, z=0),
        "floor_front": spot(0.7, 0.1, z=0),
        "floor_right": spot(1.25, 0.08, z=0),
        "floor_left": spot(-0.75, 0.1, z=0),
    }
    arrangements = [
        ["bench_l", "floor_right", "shelf_r_top", "chest_l", "rack_low", "shelf_r_low"],
        ["rack_mid", "sill", "bench_r", "floor_mid", "shelf_l_mid", "barrel"],
        ["floor_center", "shelf_l_top", "floor_front", "chest_r", "floor_left", "floor_bench"],
    ]
    place_targets(GARAGE_OBJECTS, s, arrangements)

    # Clutter around every spot.
    place("spray_paint_bottles", -0.85, ROOM_BACK - 0.2, drop=1.2, pick=["spray_paint_bottles"])
    place("Drill_01", 0.0, ROOM_BACK - 0.4, drop=1.2, rot=30)
    place("cleaner_tin_01", 0.5, ROOM_BACK - 0.15, drop=1.2)
    place("lubricant_spray", 0.6, ROOM_BACK - 0.3, drop=1.2)
    place("can_rusted", -0.25, ROOM_BACK - 0.15, drop=1.2)
    place("seeding_tray_01", -1.55, ROOM_BACK - 0.27, drop=1.4, scale=0.8)
    place("cardboard_box_01", -1.42, ROOM_BACK - 0.27, drop=0.9, scale=0.4)
    place("multi_cleaner_5_litre", -1.25, ROOM_BACK - 0.2, drop=0.5, scale=0.9)
    place("can_rusted", -2.18, ROOM_BACK - 0.2, drop=0.9, scale=0.8)
    place("cleaner_tin_01", -1.82, ROOM_BACK - 0.2, drop=1.4)
    place("plastic_jerrycan", 1.55, 1.0, z=0, rot=-20)
    place("can_rusted", -2.15, ROOM_BACK - 0.2, drop=0.25)
    place("leather_cleaner_can", 1.65, ROOM_BACK - 0.25, drop=1.1)
    place("oil_tin", 2.05, ROOM_BACK - 0.25, drop=0.6)
    place("cardboard_box_01", 1.85, ROOM_BACK - 0.3, drop=1.6, scale=0.5)
    place("small_oil_can_01", 0.05, ROOM_BACK - 0.2, drop=1.2, rot=40, scale=0.8)
    place("trowel_01", -0.35, ROOM_BACK - 0.45, drop=1.2, rot=10)
    place("measuring_tape_01", 0.95, 0.4, drop=1.0, rot=30)
    place("can_rusted", 1.0, 0.55, drop=1.0)
    place("compost_bag_02", -0.85, ROOM_BACK - 0.6, z=0, scale=0.85, rot=-15)
    place("plastic_crate_01", -2.0, ROOM_BACK - 0.27, drop=2.3, scale=0.8)
    place("cardboard_box_01", -1.42, ROOM_BACK - 0.27, drop=2.3, scale=0.5)
    place("spray_paint_bottles", 1.95, ROOM_BACK - 0.25, drop=1.1, pick=["spray_paint_bottles_dirty"])
    place("cardboard_box_01", 2.05, 0.95, z=0, scale=0.4, rot=20)
    place("cement_bag", 0.6, 1.35, z=0, rot=10, scale=0.8)
    place("metal_jerrycan", 2.1, -0.2, z=0, rot=-30)
    place("dartboard", 1.25, ROOM_BACK - 0.02, z=1.4, rot_x=90, scale=0.8)


def build_corridor():
    """Neutral corridor walked through between rooms. It ends looking through an
    open doorway into a bright, plain room that is neither study room."""
    wall = paint("hall_wall", (0.72, 0.69, 0.62))
    floor = pbr("floor_h", "plank_flooring_02", 1.2)
    trim = flat("trim", (0.8, 0.79, 0.75), 0.45)
    w, length, h = 0.85, 11.0, 2.5
    box("floor", -3, 3, -1, length, -0.2, 0, floor)
    box("ceiling", -3, 3, -1, length, h, h + 0.2, flat("ceiling", (0.9, 0.89, 0.86), 0.9))
    box("wall_l", -w - 0.2, -w, -1, 6, 0, h, wall)
    box("wall_r", w, w + 0.2, -1, 6, 0, h, wall)
    box("wall_back", -w, w, -1.2, -1, 0, h, wall)
    door_w, door_h = 0.45, 2.05
    box("door_wall_l", -3, -door_w, 6, 6.15, 0, h, wall)
    box("door_wall_r", door_w, 3, 6, 6.15, 0, h, wall)
    box("door_wall_t", -door_w, door_w, 6, 6.15, door_h, h, wall)
    box("frame_l", -door_w - 0.07, -door_w, 5.98, 6.17, 0, door_h + 0.07, trim)
    box("frame_r", door_w, door_w + 0.07, 5.98, 6.17, 0, door_h + 0.07, trim)
    box("frame_t", -door_w, door_w, 5.98, 6.17, door_h, door_h + 0.07, trim)
    box("door_leaf", door_w, door_w + 0.04, 6.17, 7.05, 0, door_h, flat("door", (0.62, 0.6, 0.55), 0.5))
    far = paint("far_wall", (0.85, 0.83, 0.78))
    box("far_l", -3.2, -3, 6, length, 0, h, far)
    box("far_r", 3, 3.2, 6, length, 0, h, far)
    box("far_back_1", -3, -0.9, length, length + 0.2, 0, h, far)
    box("far_back_2", 0.9, 3, length, length + 0.2, 0, h, far)
    box("far_back_3", -0.9, 0.9, length, length + 0.2, 0, 0.9, far)
    box("far_back_4", -0.9, 0.9, length, length + 0.2, 2.1, h, far)
    box("far_window", -0.9, 0.9, length + 0.15, length + 0.2, 0.9, 2.1, flat("sky", (0.85, 0.9, 1.0), 0.5, emit=2.5))
    box("skirt_l", -w, -w + 0.015, -1, 6, 0, 0.1, trim)
    box("skirt_r", w - 0.015, w, -1, 6, 0, 0.1, trim)
    place("hanging_picture_frame_03", -w + 0.015, 2.2, z=1.25, rot=90, scale=0.8)
    place("fancy_picture_frame_01", w - 0.015, 3.7, z=1.3, rot=-90, scale=0.6)
    place("ornate_mirror_01", -w + 0.015, 4.6, z=1.05, rot=90, scale=0.9)
    place("side_table_01", w - 0.25, 1.7, z=0, scale=0.7, rot=-90)
    place("potted_plant_04", w - 0.25, 1.7, drop=1.0)
    place("potted_plant_01", 1.7, 9.0, z=0)

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
    start, end = 0.2, 4.3
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 72
    for frame in range(1, 73):
        t = (frame - 1) / 71
        eased = t * t * (3 - 2 * t)
        cam.location.y = start + (end - start) * eased
        cam.keyframe_insert("location", frame=frame)


def report_layout():
    """Print where each scored object lands on screen, and the closest pairs."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    cam = scene.camera
    points = []
    for record in placed:
        if record["role"] != "scored":
            continue
        low, high = world_bbox(record["meshes"])
        corners = [Vector((x, y, z)) for x in (low.x, high.x) for y in (low.y, high.y) for z in (low.z, high.z)]
        proj = [world_to_camera_view(scene, cam, c) for c in corners]
        xs = [p.x * OUT_W for p in proj]
        ys = [(1 - p.y) * OUT_H for p in proj]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        points.append((record["label"], cx, cy, max(xs) - min(xs), max(ys) - min(ys)))
        print(f"LAYOUT {record['label']:18s} center=({cx:6.0f},{cy:5.0f}) size=({max(xs)-min(xs):4.0f},{max(ys)-min(ys):4.0f})")
    pairs = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = math.dist(points[i][1:3], points[j][1:3])
            pairs.append((d, points[i][0], points[j][0]))
    for d, a, b in sorted(pairs)[:6]:
        print(f"LAYOUT close {d:5.0f}px  {a} / {b}")


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
    expected = 5 if room.startswith("hallway") else 6
    if len(scored) != expected:
        raise SystemExit(f"{room}: expected {expected} scored objects, found {len(scored)}")
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


def check_visibility():
    """Quick, low-resolution version of the postprocess visibility test."""
    import numpy as np
    setup_render(800, 450, 4)
    scene = bpy.context.scene
    scene.cycles.use_denoising = False
    scored = [r for r in placed if r["role"] == "scored"]
    all_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    tmp = PREVIEW / "_check.png"
    for record in scored:
        mine = record["meshes"]
        others = [m for m in all_meshes if m not in mine]
        for m in others:
            m.visible_camera = False
        render_to(tmp, transparent=True, color_mode="RGBA")
        whole = np.array(bpy.data.images.load(str(tmp), check_existing=False).pixels[:]).reshape(-1, 4)[:, 3] > 0.25
        for m in others:
            m.visible_camera = True
            m.is_holdout = True
        render_to(PREVIEW / f"_check_{record['label'].replace(' ', '_')}.png", transparent=True, color_mode="RGBA")
        render_to(tmp, transparent=True, color_mode="RGBA")
        seen = np.array(bpy.data.images.load(str(tmp), check_existing=False).pixels[:]).reshape(-1, 4)[:, 3] > 0.25
        for m in others:
            m.is_holdout = False
        frac = (whole & seen).sum() / max(1, whole.sum())
        print(f"CHECK {record['label']:18s} visible={frac:.2f}{'  <-- LOW' if frac < 0.93 else ''}")


def render_icons(room, samples):
    """Tray icons: each scored object alone, in one neutral studio set-up.

    Same camera elevation, same light and the object's own upright pose for
    every object, so the icon carries no trace of where it stood in the room."""
    specs = [(r["name"], r["label"], r["icon"]) for r in placed if r["role"] == "scored"]
    out = RAW / room / "icons"
    out.mkdir(parents=True, exist_ok=True)
    for index, (name, label, icon) in enumerate(specs):
        target = out / f"{index:02d}.png"
        if target.exists():
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        placed.clear()
        rec = place(name, 0, 0, z=0, pick=icon["pick"], rot=icon["rot"], rot_x=icon["rot_x"])
        low, high = world_bbox(rec["meshes"])
        centre = (low + high) / 2
        size = max(high - low)
        elevation = math.radians(15)
        distance = size * 6
        bpy.ops.object.camera_add(location=(centre.x, centre.y - distance * math.cos(elevation),
                                            centre.z + distance * math.sin(elevation)))
        cam = bpy.context.active_object
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = size * 1.5
        cam.data.clip_end = distance * 4
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = cam
        world = bpy.data.worlds.new("studio")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.9, 1)
        world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
        bpy.context.scene.world = world
        bpy.ops.object.light_add(type="AREA", location=(centre.x - size * 2, centre.y - size * 3, centre.z + size * 3))
        key = bpy.context.active_object
        key.data.size = size * 4
        key.data.energy = 60 * size * size + 5
        key.rotation_euler = (centre - key.location).to_track_quat("-Z", "Y").to_euler()
        setup_render(512, 512, samples)
        bpy.context.scene.view_settings.exposure = 0.0
        render_to(target, transparent=True, color_mode="RGBA")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True,
                        choices=["kitchen", "living_room", "hallway", "corridor", "bedroom", "garage"])
    parser.add_argument("--mode", default="preview",
                        choices=["preview", "final", "transition", "icons", "check", "spots"])
    parser.add_argument("--arrangement", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--frame", type=int, default=None, help="render one transition frame")
    args = parser.parse_args(argv)
    global ARRANGEMENT, MODE
    ARRANGEMENT, MODE = args.arrangement, args.mode
    # Raw output folder: bedroom_2, garage_1, ... The corridor has no arrangements.
    room = args.scene if args.scene == "corridor" else f"{args.scene}_{args.arrangement}"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    builders = {"kitchen": build_kitchen, "living_room": build_living_room,
                "hallway": build_hallway, "corridor": build_corridor,
                "bedroom": build_bedroom, "garage": build_garage}
    builders[args.scene]()

    if args.mode == "icons":
        render_icons(room, args.samples)
    elif args.mode == "check":
        report_layout()
        check_visibility()
    elif args.mode in ("preview", "spots"):
        if args.scene != "corridor":
            report_layout()
        setup_render(960, 540, 48)
        if args.frame:
            bpy.context.scene.frame_set(args.frame)
        suffix = f"_{args.frame:02d}" if args.frame else ""
        render_to(PREVIEW / f"{room}{'_spots' if args.mode == 'spots' else ''}{suffix}.png")
    elif args.mode == "final":
        render_final(room, args.samples)
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

