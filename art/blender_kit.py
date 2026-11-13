"""Shared Blender helpers: materials, boxes, model import, lights, camera, rendering.

Imported by build_basements.py and render_objects.py, which run inside Blender.
"""
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
_DIMS_FILE = ROOT / "model_dims.json"
REAL_DIMS = json.loads(_DIMS_FILE.read_text()) if _DIMS_FILE.exists() else {}


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
    scale = scale if isinstance(scale, tuple) else (scale,) * 3
    if name in REAL_DIMS and not pick:
        # Some model files use the wrong unit (10x or 100x). Match Poly Haven's listed size.
        bpy.context.view_layer.update()
        low, high = world_bbox([o for o in new if o.type == "MESH"])
        found, listed = max(high - low), max(REAL_DIMS[name])
        if listed > 0 and not 0.33 < found / listed < 3:
            scale = tuple(v * listed / found for v in scale)
    root.scale = scale
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
