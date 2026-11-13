"""Flat drawings of the unscored clutter in the rooms. None of these is ever a decoy.
FILLER_SIZE: real longest side in metres."""
from __future__ import annotations

from .kit import band, cylinder, ellipse, gloss, mix, path, poly, rect, stroke, svg, text

DRAW = {}
FILLER_SIZE = {}


def drawing(size_m):
    def register(fn):
        DRAW[fn.__name__] = fn
        FILLER_SIZE[fn.__name__] = size_m
        return fn
    return register


@drawing(0.6)
def cardboard_box():
    tan = "#c79c63"
    return svg(240, 180,
               rect(0, 30, 180, 150, tan), path("M180,30 L240,6 L240,150 L180,180 Z", mix(tan, -0.2)),
               path("M0,30 L60,6 L240,6 L180,30 Z", mix(tan, 0.15)),
               rect(80, 30, 22, 150, "#d8b98a"), path("M80,30 L140,6 L160,6 L102,30 Z", "#e2c79c"))


@drawing(0.2)
def paint_can():
    defs, can = cylinder(4, 4, 150, 170, "#b8bcc0", top="#8f9398", cap=0.14)
    label = rect(4, 70, 150, 70, "#2f6db5") + text(79, 115, "PAINT", 26, "#ffffff")
    return svg(158, 180, can, label, gloss(18, 40, 8, 120), defs=defs)


@drawing(0.45)
def jerrycan():
    red = "#c7372a"
    body = rect(10, 40, 160, 230, red, r=14)
    side = rect(130, 40, 40, 230, mix(red, -0.2), r=10)
    x_mark = path("M30,90 L110,220 M110,90 L30,220", "none", f'stroke="{mix(red, -0.15)}" stroke-width="12"')
    handle = path("M30,40 L30,8 L120,8 L120,40 L100,40 L100,24 L50,24 L50,40 Z", mix(red, -0.1))
    spout = rect(126, 0, 30, 30, "#2a2a2a", r=4)
    return svg(180, 272, body, side, x_mark, handle, spout)


@drawing(0.2)
def spray_can():
    gid, defs = band("#2f8f5b")
    body = path("M6,40 Q6,24 22,24 L58,24 Q74,24 74,40 L74,220 L6,220 Z", f"url(#{gid})")
    cap = rect(18, 0, 44, 28, "#e0e0e0", r=6)
    return svg(80, 224, body, cap, rect(6, 120, 68, 30, "#f0e6c8"), gloss(14, 40, 6, 160), defs=defs)


@drawing(0.65)
def tire():
    return svg(260, 120, ellipse(130, 70, 128, 48, "#1c1c1e"), ellipse(130, 58, 128, 46, "#2a2a2d"),
               ellipse(130, 58, 70, 24, "#7d7f82"), ellipse(130, 62, 64, 20, "#55575a"),
               "".join(rect(18 + i * 22, 52 + (i % 2) * 4, 10, 10, "#38383c", r=2) for i in range(11)))


@drawing(0.6)
def storage_tub():
    grey = "#9fb3c8"
    return svg(260, 170, path("M10,30 L250,30 L234,166 L26,166 Z", grey, 'opacity="0.95"'),
               rect(0, 14, 260, 26, "#3a5f8a", r=6), rect(80, 4, 100, 14, "#2c4a6e", r=4),
               rect(20, 60, 220, 4, mix(grey, -0.15)), rect(28, 120, 204, 4, mix(grey, -0.15)))


@drawing(0.32)
def detergent_jug():
    orange = "#f08a24"
    body = path("M10,60 Q10,40 40,40 L130,40 Q150,40 150,60 L150,220 Q150,232 138,232 L22,232 Q10,232 10,220 Z",
                orange)
    handle = path("M96,40 L96,8 Q96,0 106,0 L136,0 Q150,0 150,16 L150,60 L128,60 L128,22 L114,22 L114,40 Z",
                  mix(orange, -0.15))
    cap = rect(28, 18, 40, 26, "#1f4fa3", r=4)
    label = rect(24, 100, 112, 90, "#ffffff", r=8) + rect(24, 120, 112, 22, "#1f4fa3")
    return svg(160, 234, body, handle, cap, label, gloss(18, 60, 8, 150, 0.35))


@drawing(0.3)
def bleach_bottle():
    gid, defs = band("#e8eef5")
    body = path("M12,70 Q12,50 32,46 L46,46 L46,20 L74,20 L74,46 L88,46 Q108,50 108,70 L108,226 Q108,236 98,236 "
                "L22,236 Q12,236 12,226 Z", f"url(#{gid})")
    cap = rect(42, 2, 36, 24, "#2a7fd4", r=5)
    label = rect(18, 120, 84, 70, "#2a7fd4", r=4) + rect(18, 140, 84, 10, "#ffffff")
    return svg(120, 238, body, cap, label, defs=defs)


@drawing(0.28)
def spray_bottle():
    gid, defs = band("#6cc2c9")
    body = path("M20,110 Q20,90 40,86 L80,86 Q100,90 100,110 L100,250 Q100,260 90,260 L30,260 Q20,260 20,250 Z",
                f"url(#{gid})")
    head = path("M36,40 L96,40 L120,60 L120,72 L96,72 L90,90 L36,90 Z", "#f2f2ee") + rect(4, 44, 34, 14, "#f2f2ee",
                                                                                       r=4)
    trigger = path("M84,72 L96,72 L92,112 L84,112 Z", "#e05d5d")
    return svg(124, 262, body, head, trigger, rect(26, 150, 68, 60, "#ffffff", r=4), defs=defs)


@drawing(0.7)
def trash_bag():
    black = "#232326"
    body = path("M40,60 Q0,90 6,170 Q10,226 70,230 L190,230 Q250,226 254,170 Q260,90 220,60 Q180,40 130,40 "
                "Q80,40 40,60 Z", black)
    knot = path("M110,46 Q100,6 120,6 L130,24 L140,6 Q160,6 150,46 Z", mix(black, 0.1))
    folds = "".join(stroke(d, "#3a3a3e", 4) for d in ("M60,90 Q80,150 70,210", "M130,70 Q140,140 130,220",
                                                         "M200,90 Q186,150 196,210"))
    return svg(260, 232, body, folds, knot, gloss(40, 100, 14, 60, 0.12))


@drawing(0.58)
def propane_tank():
    teal = "#3e8e8a"
    defs, body = cylinder(10, 70, 200, 300, teal, cap=0.1)
    dome = path("M10,90 Q10,40 110,36 Q210,40 210,90 Z", mix(teal, 0.1))
    collar = path("M50,40 L50,6 L170,6 L170,40 Q110,30 50,40 Z", mix(teal, -0.1)) + rect(90, 14, 40, 22, "#c9a227",
                                                                                         r=4)
    base = rect(20, 360, 180, 20, mix(teal, -0.3), r=4)
    return svg(220, 382, body, dome, collar, base, gloss(26, 110, 12, 210, 0.3), defs=defs)


@drawing(0.22)
def oil_can():
    gid, defs = band("#3c6e3c")
    body = rect(10, 40, 120, 160, f"url(#{gid})", r=6)
    top = poly([(10, 40), (130, 40), (120, 26), (20, 26)], "#2f572f")
    spout = rect(90, 0, 18, 30, "#c9a227", r=3)
    label = rect(10, 90, 120, 60, "#e8d27a") + text(70, 128, "OIL", 30, "#3c6e3c")
    return svg(140, 202, body, top, spout, label, defs=defs)


@drawing(0.75)
def cement_bag():
    paper = "#cdb68e"
    body = path("M10,40 Q0,20 20,14 L280,6 Q300,6 296,30 L300,140 Q302,160 280,162 L20,166 Q0,166 4,146 Z", paper)
    band_ = path("M8,70 L298,62 L299,100 L6,108 Z", "#7a8f3a")
    print_ = text(150, 92, "CEMENT", 30, "#f2ecd8")
    fold = path("M10,40 Q0,20 20,14 L280,6 Q300,6 296,30 Q150,40 10,40 Z", mix(paper, 0.12))
    return svg(304, 168, body, fold, band_, print_)


@drawing(1.4)
def wood_planks():
    wood = "#c49a62"
    planks = "".join(rect(10 + i * 34, 0 + i * 6, 30, 560 - i * 6, mix(wood, -0.06 * i), r=3)
                     + "".join(ellipse(25 + i * 34, 80 + j * 140 + i * 20, 5, 9, mix(wood, -0.3)) for j in range(3))
                     for i in range(3))
    return svg(116, 562, planks)
