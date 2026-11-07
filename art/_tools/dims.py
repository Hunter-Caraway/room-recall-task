import bpy, sys, pathlib
from mathutils import Vector
M = pathlib.Path(__file__).resolve().parents[1] / "_downloads" / "models"
names = sys.argv[sys.argv.index("--") + 1:]
for n in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(M / n / f"{n}.gltf"))
    ms = [o for o in bpy.data.objects if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
    print("DIM", n, " ".join(f"{hi[i]-lo[i]:.2f}" for i in range(3)), "meshes:", ",".join(o.name for o in ms)[:200])
