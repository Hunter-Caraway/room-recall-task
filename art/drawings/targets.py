"""Flat drawings of the 42 target objects (the BOSS photos), one function each.

Each drawing follows its photo: same object, colours, view and proportions, so the
grid's photo is the object the participant saw drawn in the room.
"""
from __future__ import annotations

import math

from .kit import band, circle, cylinder, ellipse, gloss, mix, path, poly, rect, stroke, svg, text

DRAW = {}


def drawing(fn):
    DRAW[fn.__name__.lstrip("_")] = fn
    return fn


@drawing
def mug05():
    white = "#eeeeea"
    defs, body = cylinder(10, 8, 110, 120, white, top="#c9c9c2", cap=0.14)
    inner = ellipse(65, 23, 49, 11, "#a9a9a2")
    handle = stroke("M118,40 C160,40 160,105 116,105", mix(white, -0.12), 16)
    handle_hi = stroke("M118,40 C156,40 156,105 116,105", "#ffffff", 4, 'opacity="0.6"')
    return svg(160, 136, handle, handle_hi, body, inner, gloss(22, 40, 8, 70), defs=defs)


@drawing
def bottleofwhitewine():
    gid, defs = band("#d9d27a")
    glass = path("M22,120 L22,300 Q22,312 34,312 L66,312 Q78,312 78,300 L78,120 Q78,96 60,84 L60,30 L40,30 "
                 "L40,84 Q22,96 22,120 Z", f"url(#{gid})")
    foil = rect(38, 4, 24, 52, "#c9a227", r=4) + rect(38, 46, 24, 6, "#9c7a12")
    label = rect(26, 190, 48, 80, "#f4f1e6", r=3) + rect(26, 208, 48, 4, "#c9a227")
    neck_hi = gloss(30, 110, 6, 170, 0.45)
    return svg(100, 316, glass, foil, label, neck_hi, defs=defs)


@drawing
def soccerball():
    patches = []
    for k in range(5):
        a = math.radians(k * 72 - 90)
        cx, cy = 100 + 62 * math.cos(a), 100 + 62 * math.sin(a)
        pts = [(cx + 20 * math.cos(math.radians(j * 72 + k * 72 + 90)),
                cy + 20 * math.sin(math.radians(j * 72 + k * 72 + 90))) for j in range(5)]
        patches.append(poly(pts, "#1d1d22"))
    centre = poly([(100 + 24 * math.cos(math.radians(j * 72 - 90)), 100 + 24 * math.sin(math.radians(j * 72 - 90)))
                   for j in range(5)], "#1d1d22")
    ring = circle(100, 100, 92, "#f6f6f4")
    seams = "".join(stroke(f"M{100 + 24 * math.cos(math.radians(j * 72 - 90))},{100 + 24 * math.sin(math.radians(j * 72 - 90))} "
                           f"L{100 + 52 * math.cos(math.radians(j * 72 - 90))},{100 + 52 * math.sin(math.radians(j * 72 - 90))}",
                           "#9b1c2a", 5) for j in range(5))
    shade = path("M100,8 A92,92 0 0 1 100,192 A70,92 0 0 0 100,8 Z", "#000000", 'opacity="0.12"')
    return svg(200, 200, ring, seams, centre, *patches, shade, gloss(52, 34, 22, 40, 0.5))


@drawing
def electricguitar01():
    """Red double-cutaway electric guitar, white pickguard, maple neck, front on."""
    red = "#b5121b"
    body = path("M68,262 C60,240 50,222 40,222 C22,222 10,262 16,292 C20,312 28,322 26,336 C24,352 8,366 12,388 "
                "C18,412 50,422 80,422 C112,422 146,412 150,388 C154,366 136,352 136,336 C136,320 150,308 148,290 "
                "C146,262 134,236 122,236 C112,236 100,252 92,268 Z", red)
    rim = path("M150,388 C146,412 112,422 80,422 C50,422 18,412 12,388 C30,404 56,410 80,410 C106,410 134,404 "
               "150,388 Z", mix(red, -0.3))
    shine = path("M30,250 C24,268 22,290 28,306 C32,290 36,270 44,254 Z", "#ffffff", 'opacity="0.25"')
    guard = path("M66,266 C52,262 38,280 40,302 C42,320 50,330 48,346 C46,364 56,382 78,386 C102,390 122,378 "
                 "124,360 L104,334 L98,276 Z", "#f3f2ee")
    neck = poly([(71, 48), (89, 48), (93, 300), (67, 300)], "#d9a463")
    board = poly([(73, 48), (87, 48), (89, 270), (71, 270)], "#e3b678")
    frets = "".join(rect(72, 62 + i * 19, 16 + i * 0.12, 1.6, "#bfa680") for i in range(11))
    dots = "".join(circle(80, 71 + i * 38, 2.2, "#3b2a1a") for i in range(5))
    head = path("M70,52 L70,16 C70,4 84,0 98,5 C110,10 114,20 104,26 C96,30 92,40 90,52 Z", "#d9a463")
    tuners = "".join(circle(64, 12 + i * 7, 3.6, "#d0d0d4") for i in range(6))
    pickups = "".join(rect(66, y, 28, 9, "#fbfbf8", r=4, extra=f'stroke="#d0cfc8" stroke-width="1" transform="rotate({rot} 80 {y + 4})"')
                      for y, rot in ((296, 0), (318, 0), (342, -8)))
    bridge = rect(64, 360, 32, 10, "#b8bcc2", r=2)
    knobs = circle(104, 356, 5.5, "#f3f2ee", 'stroke="#c8c7c0"') + circle(112, 370, 5.5, "#f3f2ee", 'stroke="#c8c7c0"') \
        + circle(118, 384, 5.5, "#f3f2ee", 'stroke="#c8c7c0"')
    strings = "".join(stroke(f"M{75 + i * 2},20 L{72 + i * 3.2},366", "#eeeeee", 0.7) for i in range(6))
    return svg(160, 424, body, rim, shine, guard, neck, board, frets, dots, head, tuners, pickups, bridge, knobs,
               strings)


@drawing
def coffeemaker():
    black, steel = "#232325", "#a7aab0"
    base = rect(10, 250, 160, 30, black, r=6)
    tower = rect(110, 20, 60, 240, black, r=6)
    lid = rect(14, 10, 156, 60, steel, r=8) + rect(14, 52, 156, 10, mix(steel, -0.3))
    panel = rect(124, 80, 34, 60, "#3a3a3e", r=4) + circle(141, 96, 5, "#d8d8d8") + circle(141, 122, 5, "#c0392b")
    carafe = path("M24,120 L100,120 L104,240 Q104,252 92,252 L32,252 Q20,252 20,240 Z", "#cfe0e6",
                  'opacity="0.85"')
    coffee = path("M22,190 L102,190 L104,240 Q104,252 92,252 L32,252 Q20,252 20,240 Z", "#5b3a22")
    handle = stroke("M104,140 C126,150 126,220 104,228", black, 9)
    hi = gloss(30, 128, 6, 110, 0.55)
    return svg(180, 284, base, tower, panel, lid, carafe, coffee, handle, hi)


@drawing
def hose():
    green, dark = "#2e9b4a", "#1d6b31"
    coils = "".join(ellipse(110, 108 + i * 4, 92 - i * 7, 74 - i * 6, "none",
                            f'stroke="{green if i % 2 == 0 else dark}" stroke-width="14"') for i in range(6))
    ties = rect(60, 30, 10, 60, "#f2f2f2", r=3, extra='transform="rotate(-25 65 60)"') + \
        rect(150, 30, 10, 60, "#f2f2f2", r=3, extra='transform="rotate(25 155 60)"')
    end = stroke("M40,150 C50,190 80,200 110,206", green, 14) + rect(104, 196, 26, 18, "#c99a2e", r=3)
    return svg(220, 220, coils, ties, end)


@drawing
def washingmachine():
    """White top-loading washer: plain front, lid on top, control panel at the back."""
    white = "#f0f1f2"
    panel = rect(10, 0, 180, 46, "#dfe2e6", r=6) + rect(70, 12, 60, 18, "#1e3247", r=3) + \
        circle(160, 22, 11, "#b8bcc2") + circle(36, 22, 7, "#b8bcc2") + rect(10, 38, 180, 8, mix(white, -0.18))
    top = poly([(10, 46), (190, 46), (198, 80), (2, 80)], mix(white, -0.04))
    lid = poly([(34, 52), (166, 52), (172, 74), (28, 74)], mix(white, -0.12)) + rect(84, 60, 32, 6, "#c4c8cd", r=3)
    front = rect(2, 80, 196, 196, white, r=4)
    side_shade = rect(160, 80, 38, 196, "#000000", r=4, extra='opacity="0.07"')
    seam = rect(14, 96, 172, 3, mix(white, -0.1)) + rect(14, 250, 172, 3, mix(white, -0.1))
    feet = rect(14, 274, 20, 8, "#555", r=2) + rect(166, 274, 20, 8, "#555", r=2)
    return svg(200, 284, panel, top, lid, front, side_shade, seam, feet)


@drawing
def key07():
    brass, dark = "#c9a33a", "#8e6f1c"
    ring = circle(120, 40, 30, "none", f'stroke="#b9b9bd" stroke-width="7"')
    keys = []
    for k, ang in enumerate((-40, -15, 10, 35)):
        keys.append(f'<g transform="rotate({ang} 120 60)">'
                    + rect(108, 60, 24, 26, brass if k % 2 == 0 else mix(brass, -0.1), r=8)
                    + circle(120, 70, 4, dark)
                    + path("M114,86 L126,86 L126,170 L120,178 L114,170 L114,150 L108,146 L114,140 L108,132 "
                           "L114,126 Z", brass if k % 2 == 0 else mix(brass, -0.1)) + "</g>")
    return svg(240, 200, *keys, ring)


@drawing
def tabascosauce():
    sauce = "#9b2a1a"
    gid, defs = band(sauce)
    bottle = path("M18,90 Q18,70 34,62 L34,40 L50,40 L50,62 Q66,70 66,90 L66,200 Q66,210 56,210 L28,210 "
                  "Q18,210 18,200 Z", f"url(#{gid})")
    cap = rect(32, 4, 20, 38, "#e9e2cf", r=3) + rect(32, 30, 20, 4, "#1e7a3a")
    label = rect(20, 112, 44, 70, "#efe6c8", r=2) + rect(20, 126, 44, 14, "#1e7a3a")
    return svg(84, 212, bottle, cap, label, gloss(24, 90, 5, 100, 0.4), defs=defs)
