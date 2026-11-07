import sys, pathlib
sys.argv = [sys.argv[0], "--", "--scene", "living_room", "--mode", "preview"]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bpy
import build_rooms as b
bpy.ops.wm.read_factory_settings(use_empty=True)
b.place("wooden_bookshelf_worn", -1.6, b.ROOM_BACK - 0.3, z=0)
z = 2.5
out = []
while z > 0.05:
    hit = b.surface_below(-1.6, b.ROOM_BACK - 0.3, z)
    out.append(round(hit, 3)); z = hit - 0.05
print("SHELVES", out)
