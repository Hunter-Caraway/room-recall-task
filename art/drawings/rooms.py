"""Flat drawings of the basements, with their spots and filler.

Canvas 1600 x 900. One-point perspective: the back wall is 4 m wide (270 px per metre),
the floor runs forward to the bottom of the picture, and a table or bench in the
foreground (about 550 px per metre) fills the lower edge, for the smallest objects.

Spots are where an object can be: x, y is the bottom centre of an object standing
there, or the top centre of an object hanging from a wall hook (just under the hook).
Each room function returns (picture svg, spots, filler); filler is a list of
(drawing name, x, y bottom centre, px per metre), composited by build_drawn.py.
"""
from __future__ import annotations

from .kit import circle, ellipse, mix, poly, rect, stroke, svg

W, H = 1600, 900
BACK = (260, 40, 1340, 580)  # back wall: left, top, right, floor line
WALL_PX = 270  # px per metre on the back wall
TABLE_BACK, TABLE_FRONT, TABLE_PX = 730, 806, 550
TABLE_Y = 782  # where objects stand on the table top
HOOK_DROP = 10  # a hanging object's top sits this far under the hook's centre


def floor_px(y: float) -> float:
    """Pixels per metre on the floor at screen height y (linear in perspective, near enough)."""
    return WALL_PX + (y - BACK[3]) / (H - BACK[3]) * (400 - WALL_PX)


def shell(wall: str, floor: str, side: str, ceiling: str = "#d8d4cc", skirting: str = "#e8e4dc") -> str:
    l, t, r, b = BACK
    return "".join([
        rect(0, 0, W, H, ceiling),
        poly([(0, H), (l, b), (r, b), (W, H)], floor),
        poly([(0, 0), (l, t), (l, b), (0, H)], side),
        poly([(W, 0), (r, t), (r, b), (W, H)], mix(side, -0.06)),
        rect(l, t, r - l, b - t, wall),
        rect(l, b - 14, r - l, 14, skirting),
        poly([(0, H), (l, b), (l, b - 14), (0, H - 40)], mix(skirting, -0.1)),
        poly([(W, H), (r, b), (r, b - 14), (W, H - 40)], mix(skirting, -0.15)),
    ])


def ceiling_light(x, y=40):
    return rect(x - 4, 0, 8, y - 6, "#555") + ellipse(x, y, 40, 14, "#f6f0d6") + ellipse(x, y - 6, 40, 8, "#d8d2bc")


def pipe(x0, y0, x1, y1, colour="#8a8f95", w=12):
    return stroke(f"M{x0},{y0} L{x1},{y1}", colour, w) + stroke(f"M{x0},{y0} L{x1},{y1}", mix(colour, 0.3), 3)


def hook(x, y, colour="#2b2b2e"):
    return rect(x - 10, y - 18, 20, 10, mix(colour, 0.2), r=3) + stroke(f"M{x},{y - 10} L{x},{y} Q{x},{y + 8} {x + 8},{y + 4}",
                                                                         colour, 5)


def metal_shelving(x0, x1, boards, post="#3a3d42", board="#8f949b"):
    parts = []
    for y in boards:
        parts.append(rect(x0, y - 4, x1 - x0, 12, board) + rect(x0, y - 4, x1 - x0, 4, mix(board, 0.25)))
    for x in (x0, x1 - 10):
        parts.append(rect(x, boards[0] - 40, 10, BACK[3] - boards[0] + 40, post))
    return "".join(parts)


def wood_shelf(x0, x1, y, wood="#b07a45"):
    return (rect(x0, y - 4, x1 - x0, 14, wood) + rect(x0, y - 4, x1 - x0, 4, mix(wood, 0.25))
            + rect(x0 + 20, y + 10, 8, 26, mix(wood, -0.3)) + rect(x1 - 28, y + 10, 8, 26, mix(wood, -0.3)))


def table(top="#c8955a", apron="#a5743f"):
    """The foreground table top seen from above at a slant, its front edge, and the apron."""
    return (poly([(-20, TABLE_FRONT), (40, TABLE_BACK), (W - 40, TABLE_BACK), (W + 20, TABLE_FRONT)], top)
            + rect(40, TABLE_BACK, W - 80, 4, mix(top, -0.12))
            + rect(-20, TABLE_FRONT, W + 40, 18, mix(top, 0.18))
            + rect(-20, TABLE_FRONT + 18, W + 40, H - TABLE_FRONT, apron)
            + rect(-20, TABLE_FRONT + 18, W + 40, 8, mix(apron, -0.25)))


def socket(x, y):
    return rect(x, y, 30, 30, "#f1efe9", r=3) + rect(x + 9, y + 9, 3, 8, "#666") + rect(x + 18, y + 9, 3, 8, "#666")


def window(x, y, w, h):
    return (rect(x, y, w, h, "#e8e4dc") + rect(x + 8, y + 8, w - 16, h - 16, "#bcd7e6")
            + rect(x + w / 2 - 3, y + 8, 6, h - 16, "#e8e4dc") + rect(x + 8, y + 8, (w - 16) / 2 - 3, 10, "#d6e8f0"))


def door(x, w=200, top=180, colour="#9c7a54"):
    return (rect(x - 10, top - 10, w + 20, BACK[3] - top + 10 - 14, "#e8e4dc") + rect(x, top, w, BACK[3] - top - 14, colour)
            + rect(x + 20, top + 20, w - 40, 140, mix(colour, -0.08)) + rect(x + 20, top + 190, w - 40, 160,
                                                                             mix(colour, -0.08))
            + circle(x + w - 26, top + 190, 8, "#c9a227"))


def spot(id_, surface, x, y, px, w, h):
    return {"id": id_, "surface": surface, "x": x, "y": y, "px_per_m": round(px, 1), "max_w_m": w, "max_h_m": h}


def wall_spot(id_, x, y, w=0.6, h=1.0):
    return spot(id_, "wall", x, y + HOOK_DROP, WALL_PX, w, h)


def table_spots(xs, w=0.5, h=0.5):
    return [spot(f"table_{j}", "table", x, TABLE_Y, TABLE_PX, w, h) for j, x in enumerate(xs)]


def floor_spot(id_, x, y, w=0.75, h=1.05):
    return spot(id_, "floor", x, y, floor_px(y), w, h)


def storage():
    shelves_a = (190, 320, 450)
    shelves_b = (270, 420)
    hooks = ((760, 140), (900, 140))
    picture = svg(W, H,
                  shell(wall="#9a958c", floor="#8a8c8e", side="#85817a"),
                  "".join(rect(BACK[0], y, BACK[2] - BACK[0], 3, "#8b867d") for y in range(80, 566, 54)),
                  ceiling_light(800), pipe(BACK[0], 70, BACK[2], 70),
                  metal_shelving(300, 640, shelves_a),
                  wood_shelf(1010, 1310, shelves_b[0]), wood_shelf(1010, 1310, shelves_b[1]),
                  *[hook(x, y) for x, y in hooks], socket(950, 470),
                  table())
    spots = [
        *[spot(f"shelf_a{i}_{j}", "shelf", x, y - 4, WALL_PX, 0.55, 0.42)
          for i, y in enumerate(shelves_a) for j, x in enumerate((385, 555))],
        *[spot(f"shelf_b{i}_{j}", "shelf", x, y - 4, WALL_PX, 0.5, 0.5)
          for i, y in enumerate(shelves_b) for j, x in enumerate((1090, 1230))],
        wall_spot("wall_a", *hooks[0]), wall_spot("wall_b", *hooks[1]),
        spot("lean_a", "lean", 700, 578, WALL_PX, 0.5, 1.3),
        spot("lean_b", "lean", 960, 578, WALL_PX, 0.5, 1.3),
        floor_spot("floor_l", 430, 650), floor_spot("floor_m", 820, 640), floor_spot("floor_r", 1180, 660),
        *table_spots((300, 620, 940, 1260)),
    ]
    filler = [("cardboard_box", 1440, 705, floor_px(705)), ("paint_can", 470, 446, WALL_PX),
              ("jerrycan", 170, 712, floor_px(712)), ("spray_can", 1250, 416, WALL_PX)]
    return picture, spots, filler


def laundry():
    tiles = "".join(rect(BACK[0], y, BACK[2] - BACK[0], 2, "#b5c4cc") for y in range(70, 566, 40)) + \
        "".join(rect(x, BACK[1], 2, BACK[3] - BACK[1] - 14, "#b5c4cc") for x in range(300, 1340, 40))
    shelf_y = (230, 380)
    hooks = ((560, 130), (700, 130), (1220, 150))
    sink = (rect(860, 330, 240, 90, "#eef0f2", r=8) + rect(870, 330, 220, 16, "#d6dade", r=4)
            + rect(880, 420, 20, 146, "#c4c8cd") + rect(1060, 420, 20, 146, "#c4c8cd")
            + stroke("M980,330 L980,290 Q980,280 1000,280 L1010,280", "#9ea3a8", 8))
    picture = svg(W, H,
                  shell(wall="#cdd8de", floor="#9a9690", side="#bcc7cc"),
                  tiles, window(300, 70, 200, 110), ceiling_light(800),
                  pipe(1310, BACK[1], 1310, 560), pipe(BACK[0], 60, 1310, 60),
                  wood_shelf(290, 520, shelf_y[0]), wood_shelf(290, 520, shelf_y[1]),
                  *[hook(x, y) for x, y in hooks], sink, socket(1160, 470),
                  table(top="#d9d4cc", apron="#b9b2a6"))
    spots = [
        *[spot(f"shelf_{i}_{j}", "shelf", x, y - 4, WALL_PX, 0.5, 0.45)
          for i, y in enumerate(shelf_y) for j, x in enumerate((350, 460))],
        spot("sink_ledge", "shelf", 1040, 326, WALL_PX, 0.4, 0.4),
        wall_spot("wall_a", *hooks[0]), wall_spot("wall_b", *hooks[1]), wall_spot("wall_c", *hooks[2]),
        spot("lean_a", "lean", 780, 578, WALL_PX, 0.5, 1.3),
        spot("lean_b", "lean", 1180, 578, WALL_PX, 0.5, 1.3),
        floor_spot("floor_l", 380, 680), floor_spot("floor_m", 760, 650), floor_spot("floor_r", 1150, 680),
        *table_spots((280, 600, 920, 1240)),
    ]
    filler = [("detergent_jug", 460, 376, WALL_PX), ("bleach_bottle", 1460, 712, floor_px(712)),
              ("spray_bottle", 920, 326, WALL_PX), ("trash_bag", 150, 712, floor_px(712))]
    return picture, spots, filler


def workshop():
    pegboard = rect(470, 90, 560, 330, "#c9a77a") + "".join(
        circle(x, y, 2.5, "#8e6f48") for x in range(490, 1020, 24) for y in range(110, 410, 24))
    hooks = ((600, 130), (750, 130), (900, 130))
    shelves = (230, 380)
    picture = svg(W, H,
                  shell(wall="#a9a39a", floor="#7d7b78", side="#99938a"),
                  "".join(rect(BACK[0], y, BACK[2] - BACK[0], 3, "#9a948a") for y in range(80, 566, 54)),
                  pegboard, ceiling_light(560), ceiling_light(1040), door(300, 140, 230),
                  metal_shelving(1080, 1320, shelves),
                  *[hook(x, y) for x, y in hooks], socket(1040, 470),
                  table(top="#8f6a43", apron="#6f5133"))
    spots = [
        *[spot(f"shelf_{i}_{j}", "shelf", x, y - 4, WALL_PX, 0.5, 0.45)
          for i, y in enumerate(shelves) for j, x in enumerate((1150, 1250))],
        *[wall_spot(f"wall_{k}", x, y) for k, (x, y) in zip("abc", hooks)],
        spot("lean_a", "lean", 1000, 578, WALL_PX, 0.5, 1.3),
        spot("lean_b", "lean", 520, 578, WALL_PX, 0.5, 1.3),
        floor_spot("floor_l", 420, 690), floor_spot("floor_m", 780, 660), floor_spot("floor_r", 1170, 680),
        *table_spots((300, 620, 940, 1260)),
    ]
    filler = [("tire", 1430, 712, floor_px(712)), ("propane_tank", 160, 712, floor_px(712)),
              ("oil_can", 1250, 376, WALL_PX), ("wood_planks", 1300, 578, WALL_PX)]
    return picture, spots, filler


def practice():
    shelf_y = 300
    hooks = ((800, 140),)
    picture = svg(W, H,
                  shell(wall="#d8cdb8", floor="#a08f78", side="#c9bea8"),
                  window(1050, 90, 220, 130), ceiling_light(800),
                  wood_shelf(320, 660, shelf_y), *[hook(x, y) for x, y in hooks],
                  table(top="#b88a5a", apron="#956b40"))
    spots = [
        *[spot(f"shelf_{j}", "shelf", x, shelf_y - 4, WALL_PX, 0.5, 0.5) for j, x in enumerate((400, 580))],
        wall_spot("wall_a", *hooks[0]),
        floor_spot("floor_l", 520, 660), floor_spot("floor_r", 1100, 660),
        *table_spots((320, 700, 1080)),
    ]
    filler = [("storage_tub", 1420, 712, floor_px(712)), ("cement_bag", 200, 712, floor_px(712))]
    return picture, spots, filler


ROOMS = {"storage": storage, "laundry": laundry, "workshop": workshop, "practice": practice}
