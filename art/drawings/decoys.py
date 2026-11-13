"""Flat drawings of the decoys: everyday objects shown only in the recognition grid.

None is a BOSS object, a filler or a practice object. Many share a category with a
target (another ball, another cup, another hand tool) so a participant cannot pick the
targets by kind alone. DECOYS maps name -> (label, category, real longest side in metres).
"""
from __future__ import annotations

import math

from .kit import band, circle, cylinder, ellipse, gloss, mix, path, poly, rect, stroke, svg, text

DRAW = {}
DECOYS = {}


def decoy(label, category, size_m):
    def register(fn):
        DRAW[fn.__name__] = fn
        DECOYS[fn.__name__] = (label, category, size_m)
        return fn
    return register


def _shade_ball(cx, cy, r, opacity=0.18):
    return path(f"M{cx},{cy - r} A{r},{r} 0 0 1 {cx},{cy + r} A{r * 0.72},{r} 0 0 0 {cx},{cy - r} Z", "#000000",
                f'opacity="{opacity}"')


# ---- balls and sport -------------------------------------------------------------------

@decoy("basketball", "ball", 0.24)
def basketball():
    orange, line = "#e2742b", "#3a2216"
    seams = (stroke("M100,4 L100,196", line, 4) + stroke("M4,100 L196,100", line, 4)
             + stroke("M30,30 C70,70 70,130 30,170", line, 4) + stroke("M170,30 C130,70 130,130 170,170", line, 4))
    return svg(200, 200, circle(100, 100, 96, orange), seams, _shade_ball(100, 100, 96), gloss(44, 40, 18, 30, 0.35))


@decoy("baseball", "ball", 0.075)
def baseball():
    red = "#c8242c"
    stitches = "".join(stroke(f"M{x - 6},{y - 4} L{x + 6},{y + 4}", red, 3) for x, y in
                       ((40, 50), (34, 80), (34, 112), (40, 144), (160, 50), (166, 80), (166, 112), (160, 144)))
    seams = stroke("M50,20 C20,70 20,130 50,180", red, 3) + stroke("M150,20 C180,70 180,130 150,180", red, 3)
    return svg(200, 200, circle(100, 100, 96, "#f4f1e8"), seams, stitches, _shade_ball(100, 100, 96, 0.14),
               gloss(56, 40, 18, 30, 0.5))


@decoy("tennis ball", "ball", 0.067)
def tennis_ball():
    return svg(200, 200, circle(100, 100, 96, "#cfe03a"),
               stroke("M14,60 C80,80 80,120 14,140", "#f6f6ee", 8) + stroke("M186,60 C120,80 120,120 186,140",
                                                                            "#f6f6ee", 8),
               _shade_ball(100, 100, 96), gloss(56, 40, 18, 30, 0.4))


@decoy("beach ball", "ball", 0.4)
def beach_ball():
    colours = ["#e63946", "#f4f1e8", "#2a7fd4", "#f4f1e8", "#f6c026", "#f4f1e8"]
    wedges = []
    for k, c in enumerate(colours):
        a0, a1 = math.radians(k * 60 - 90), math.radians(k * 60 - 30)
        wedges.append(path(f"M100,100 L{100 + 96 * math.cos(a0)},{100 + 96 * math.sin(a0)} "
                           f"A96,96 0 0 1 {100 + 96 * math.cos(a1)},{100 + 96 * math.sin(a1)} Z", c))
    return svg(200, 200, *wedges, circle(100, 100, 14, "#f4f1e8"), _shade_ball(100, 100, 96, 0.14),
               gloss(50, 40, 18, 30, 0.4))


@decoy("baseball bat", "sports", 0.84)
def baseball_bat():
    wood = "#d2a265"
    gid, defs = band(wood, horizontal=False)
    bat = path("M10,52 L40,48 Q200,40 380,34 Q420,32 420,50 Q420,68 380,66 Q200,60 40,56 L10,58 Z", f"url(#{gid})")
    knob = ellipse(10, 54, 8, 14, mix(wood, -0.2))
    grip = rect(20, 46, 70, 12, "#2a2a2e", r=4)
    return svg(430, 100, bat, grip, knob, defs=defs)


@decoy("skateboard", "sports", 0.8)
def skateboard():
    deck = rect(10, 30, 400, 60, "#2a6f97", r=30) + rect(30, 40, 360, 40, "#2b2b2f", r=20)
    trucks = rect(70, 92, 40, 10, "#9ea3a8") + rect(310, 92, 40, 10, "#9ea3a8")
    wheels = "".join(circle(x, 108, 14, "#f2e3a6") for x in (66, 114, 306, 354))
    return svg(420, 124, trucks, wheels, deck, text(210, 70, "SK8", 26, "#f2e3a6"))


@decoy("dumbbell", "sports", 0.3)
def dumbbell():
    grey = "#3a3d42"
    bar = rect(60, 54, 180, 16, "#b8bcc2", r=4)
    plates = "".join(rect(x, 14, 30, 96, grey, r=8) + rect(x + 4, 18, 8, 88, mix(grey, 0.3), r=3)
                     for x in (20, 54, 216, 250))
    return svg(300, 124, bar, plates)


@decoy("boxing glove", "sports", 0.3)
def boxing_glove():
    red = "#c81d25"
    body = path("M40,60 Q40,10 110,10 Q190,10 190,90 Q190,160 120,170 L60,170 Q30,160 30,120 Z", red)
    thumb = path("M40,80 Q0,90 8,130 Q16,150 40,140 Z", mix(red, -0.15))
    cuff = rect(56, 160, 110, 50, "#f2f2ee", r=8) + rect(56, 176, 110, 8, "#d6d6d0")
    return svg(200, 214, body, thumb, cuff, gloss(70, 30, 50, 20, 0.3))


@decoy("hockey stick", "sports", 1.5)
def hockey_stick():
    shaft = poly([(150, 0), (164, 0), (60, 340), (46, 340)], "#d9b27a")
    blade = path("M46,330 L66,336 Q60,370 10,372 Q0,372 2,360 Q20,356 46,330 Z", "#2a2a2e")
    tape = rect(144, 0, 22, 40, "#2a2a2e", r=3, extra='transform="rotate(17 155 20)"')
    return svg(170, 376, shaft, tape, blade)


# ---- cups, bottles, kitchen ------------------------------------------------------------

@decoy("teapot", "kitchen tool", 0.25)
def teapot():
    blue = "#3d6fa6"
    body = ellipse(130, 130, 90, 70, blue)
    lid = path("M80,70 Q130,40 180,70 Z", mix(blue, 0.1)) + circle(130, 46, 10, mix(blue, -0.2))
    spout = path("M46,120 Q10,110 4,60 L18,58 Q30,100 60,100 Z", blue)
    handle = stroke("M216,100 C260,100 260,170 210,170", mix(blue, -0.15), 14)
    return svg(260, 204, spout, handle, body, lid, _shade_ball(130, 130, 70, 0.12), gloss(80, 100, 12, 50, 0.35))


@decoy("frying pan", "kitchen tool", 0.45)
def frying_pan():
    black = "#26272b"
    pan = ellipse(110, 70, 104, 54, black) + ellipse(110, 64, 92, 44, "#3c3e44")
    handle = rect(200, 54, 160, 22, black, r=10) + circle(344, 65, 5, "#55575c")
    return svg(370, 130, handle, pan, gloss(60, 40, 50, 8, 0.2))


@decoy("toaster", "kitchen appliance", 0.3)
def toaster():
    steel = "#c6cacf"
    gid, defs = band(steel)
    body = rect(10, 40, 260, 160, f"url(#{gid})", r=40)
    slots = rect(60, 40, 60, 10, "#3a3a3e", r=4) + rect(160, 40, 60, 10, "#3a3a3e", r=4)
    toast = rect(68, 10, 44, 36, "#d9a35a", r=10) + rect(168, 14, 44, 32, "#d9a35a", r=10)
    lever = rect(250, 110, 30, 12, "#2a2a2e", r=4)
    feet = rect(30, 198, 30, 8, "#2a2a2e", r=3) + rect(220, 198, 30, 8, "#2a2a2e", r=3)
    return svg(290, 208, toast, body, slots, lever, feet, defs=defs)


@decoy("kettle", "kitchen appliance", 0.28)
def kettle():
    red = "#d64545"
    body = path("M40,80 L200,80 L220,230 Q220,250 200,250 L40,250 Q20,250 20,230 Z", red)
    handle = path("M50,80 Q50,20 120,20 Q190,20 190,80 L170,80 Q170,40 120,40 Q70,40 70,80 Z", "#2a2a2e")
    spout = path("M200,110 L250,90 L254,104 L214,140 Z", red)
    base = rect(16, 244, 208, 16, "#2a2a2e", r=6)
    return svg(260, 262, handle, spout, body, base, gloss(40, 100, 12, 120, 0.35))


@decoy("whisk", "kitchen tool", 0.3)
def whisk():
    wires = "".join(stroke(f"M60,170 C{60 + d},120 {60 + d * 1.4},40 60,10", "#c4c8cd", 3)
                    for d in (-40, -24, -8, 8, 24, 40))
    handle = rect(48, 166, 24, 110, "#c03a2b", r=10)
    return svg(120, 280, wires, handle)


@decoy("rolling pin", "kitchen tool", 0.45)
def rolling_pin():
    wood = "#deb887"
    gid, defs = band(wood, horizontal=False)
    return svg(420, 80, rect(10, 32, 70, 16, mix(wood, -0.2), r=8), rect(340, 32, 70, 16, mix(wood, -0.2), r=8),
               rect(70, 10, 280, 60, f"url(#{gid})", r=12), defs=defs)


@decoy("blender", "kitchen appliance", 0.4)
def blender():
    jar = path("M40,20 L160,20 L140,220 L60,220 Z", "#cfe0e6", 'opacity="0.9"')
    lid = rect(34, 6, 132, 20, "#2a2a2e", r=6)
    smoothie = path("M48,110 L152,110 L140,220 L60,220 Z", "#e35d8a")
    base = path("M40,220 L160,220 L176,320 L24,320 Z", "#2a2a2e") + circle(100, 270, 16, "#9ea3a8")
    return svg(200, 324, jar, smoothie, lid, base, gloss(56, 40, 10, 150, 0.45))


@decoy("wine glass", "cup", 0.2)
def wine_glass():
    glass = "#dfeef2"
    bowl = path("M20,10 L140,10 Q144,110 80,130 Q16,110 20,10 Z", glass, 'opacity="0.85"')
    wine = path("M24,60 L136,60 Q130,116 80,128 Q30,116 24,60 Z", "#7a1d2e")
    stem = rect(76, 128, 8, 110, glass) + ellipse(80, 240, 50, 10, glass)
    return svg(160, 252, bowl, wine, stem, gloss(34, 20, 8, 60, 0.6))


@decoy("teacup and saucer", "cup", 0.15)
def teacup():
    white = "#f4f1ea"
    saucer = ellipse(110, 150, 104, 20, mix(white, -0.08)) + ellipse(110, 146, 70, 12, mix(white, -0.15))
    cup = path("M30,40 L190,40 Q186,140 110,146 Q34,140 30,40 Z", white)
    rim = ellipse(110, 40, 80, 12, "#c79a6a")
    trim = stroke("M38,70 Q110,90 182,70", "#5a8fc9", 6)
    handle = stroke("M184,60 C226,60 226,120 176,116", white, 12)
    return svg(220, 174, saucer, handle, cup, rim, trim)


@decoy("ketchup bottle", "bottle", 0.22)
def ketchup_bottle():
    red = "#c8201e"
    gid, defs = band(red)
    body = path("M20,70 Q20,50 40,46 L80,46 Q100,50 100,70 L100,250 Q100,262 88,262 L32,262 Q20,262 20,250 Z",
                f"url(#{gid})")
    cap = rect(32, 4, 56, 46, "#f2f2ee", r=8)
    label = rect(20, 120, 80, 80, "#f2f2ee", r=6) + poly([(60, 132), (78, 160), (60, 188), (42, 160)], "#3a8f3a")
    return svg(120, 264, body, cap, label, defs=defs)


@decoy("water bottle", "bottle", 0.25)
def water_bottle():
    blue = "#4aa3df"
    gid, defs = band(blue)
    body = rect(10, 50, 90, 220, f"url(#{gid})", r=20)
    cap = rect(26, 10, 58, 46, "#2a2a2e", r=8) + stroke("M50,14 C50,-6 90,-6 86,24", "#2a2a2e", 6)
    return svg(110, 272, body, cap, rect(10, 140, 90, 6, mix(blue, -0.3)), defs=defs)


@decoy("milk carton", "food", 0.25)
def milk_carton():
    white, blue = "#f6f6f2", "#2f6db5"
    front = rect(10, 80, 120, 200, white) + rect(130, 80, 50, 200, mix(white, -0.12))
    roof = poly([(10, 80), (70, 30), (130, 80)], mix(white, -0.06)) + poly([(70, 30), (130, 80), (180, 80),
                                                                            (120, 30)], mix(white, -0.18))
    fin = rect(64, 10, 62, 22, mix(white, -0.06))
    label = rect(10, 150, 120, 60, blue) + text(70, 190, "MILK", 28, "#ffffff")
    return svg(190, 282, front, roof, fin, label)


@decoy("cereal box", "food", 0.3)
def cereal_box():
    yellow = "#f2c12e"
    front = rect(10, 10, 160, 260, yellow) + rect(170, 10, 30, 260, mix(yellow, -0.25))
    bowl = path("M40,170 L140,170 Q136,220 90,224 Q44,220 40,170 Z", "#f2f2ee")
    flakes = "".join(ellipse(56 + i * 14, 166 - (i % 2) * 6, 9, 5, "#d98a2b") for i in range(7))
    title = rect(24, 30, 132, 50, "#d62828", r=8) + text(90, 66, "CRUNCH", 22, "#ffffff")
    return svg(204, 274, front, title, flakes, bowl)


@decoy("banana", "food", 0.2)
def banana():
    yellow = "#f4d03f"
    body = path("M20,40 Q40,160 200,170 Q250,170 270,150 Q200,150 120,110 Q60,80 40,30 Z", yellow)
    shade = path("M40,30 Q60,80 120,110 Q200,150 270,150 Q250,160 200,160 Q100,150 40,30 Z", mix(yellow, -0.2))
    tips = rect(14, 20, 24, 20, "#5b4a2a", r=4) + circle(272, 150, 6, "#3a2a1a")
    return svg(290, 180, body, shade, tips)


@decoy("apple", "food", 0.08)
def apple():
    red = "#c8242c"
    body = path("M100,50 C40,10 0,70 20,130 C40,190 80,200 100,186 C120,200 160,190 180,130 C200,70 160,10 100,50 Z",
                red)
    stem = stroke("M100,52 Q104,24 116,10", "#5b3a1a", 6)
    leaf = path("M108,30 Q140,0 168,18 Q140,44 108,30 Z", "#3a8f3a")
    return svg(200, 200, body, stem, leaf, gloss(46, 70, 16, 40, 0.35))


@decoy("honey jar", "food", 0.12)
def honey_jar():
    honey = "#e0a526"
    gid, defs = band(honey)
    jar = rect(14, 50, 152, 150, f"url(#{gid})", r=24)
    lid = rect(24, 20, 132, 36, "#f2f2ee", r=6) + "".join(rect(28 + i * 16, 20, 4, 36, "#d8d2c4") for i in range(8))
    label = rect(30, 100, 120, 60, "#f2f2ee", r=6) + text(90, 140, "HONEY", 22, "#8a5a10")
    return svg(180, 204, jar, lid, label, defs=defs)


# ---- tools and hardware ----------------------------------------------------------------

@decoy("hammer", "hand tool", 0.33)
def hammer():
    head = path("M10,20 L150,20 L150,70 L60,70 Q30,70 10,50 Z", "#6b6f75") + rect(140, 20, 14, 50, "#55595e")
    handle = rect(70, 66, 26, 220, "#c78a4a", r=8) + rect(70, 220, 26, 66, "#2a2a2e", r=8)
    return svg(170, 290, handle, head, gloss(20, 26, 100, 8, 0.3))


@decoy("screwdriver", "hand tool", 0.22)
def screwdriver():
    handle = path("M20,40 Q20,10 50,10 L150,14 Q170,20 170,50 Q170,80 150,86 L50,90 Q20,90 20,60 Z", "#f2c12e")
    grooves = "".join(rect(60 + i * 20, 22, 8, 56, mix("#f2c12e", -0.2), r=4) for i in range(4))
    shaft = rect(168, 42, 200, 16, "#b8bcc2") + poly([(368, 42), (392, 46), (392, 54), (368, 58)], "#9ea3a8")
    return svg(400, 100, shaft, handle, grooves)


@decoy("pliers", "hand tool", 0.2)
def pliers():
    jaws = poly([(80, 0), (100, 0), (106, 90), (94, 90)], "#9ea3a8") + poly([(120, 0), (140, 0), (126, 90),
                                                                           (114, 90)], "#8a8f95")
    pivot = circle(110, 100, 18, "#7d8288")
    handles = (path("M100,110 Q70,200 40,300 L66,306 Q94,210 112,116 Z", "#2f6db5")
               + path("M120,110 Q150,200 180,300 L154,306 Q126,210 108,116 Z", mix("#2f6db5", -0.15)))
    return svg(220, 310, handles, jaws, pivot, circle(110, 100, 6, "#55595e"))


@decoy("hand saw", "hand tool", 0.6)
def hand_saw():
    blade = poly([(110, 30), (440, 70), (440, 100), (110, 130)], "#c4c8cd")
    teeth = "".join(poly([(110 + i * 22, 130 - i * 2.7), (121 + i * 22, 142 - i * 3), (132 + i * 22,
                                                                                     130 - i * 2.9)], "#9ea3a8")
                    for i in range(15))
    handle = path("M10,20 Q10,0 30,0 L110,10 L120,140 L30,150 Q10,150 10,130 Z", "#b5651d")
    hole = path("M36,40 L90,40 L94,110 L36,116 Z", "#ffffff")
    return svg(450, 160, blade, teeth, handle, hole)


@decoy("tape measure", "hand tool", 0.08)
def tape_measure():
    yellow = "#f2c12e"
    body = rect(10, 10, 170, 170, yellow, r=30) + circle(95, 95, 46, mix(yellow, -0.2)) + circle(95, 95, 14,
                                                                                                "#2a2a2e")
    tape = rect(176, 140, 60, 18, "#f6e27a") + rect(232, 132, 8, 32, "#9ea3a8")
    marks = "".join(rect(184 + i * 10, 140, 2, 8, "#2a2a2e") for i in range(5))
    return svg(244, 190, tape, marks, body, rect(20, 150, 40, 20, "#2a2a2e", r=4))


@decoy("flashlight", "hardware", 0.2)
def flashlight():
    gid, defs = band("#2a2a2e", horizontal=False)
    body = rect(10, 40, 220, 50, f"url(#{gid})", r=10)
    head = poly([(220, 30), (300, 10), (300, 120), (220, 100)], "#3a3a3e") + ellipse(300, 65, 12, 55, "#f6e27a")
    button = rect(120, 30, 30, 14, "#d62828", r=4)
    return svg(316, 130, body, button, head, defs=defs)


@decoy("padlock", "hardware", 0.07)
def padlock():
    shackle = path("M40,100 L40,60 Q40,10 100,10 Q160,10 160,60 L160,100 L136,100 L136,60 Q136,34 100,34 "
                   "Q64,34 64,60 L64,100 Z", "#b8bcc2")
    gid, defs = band("#c9a227")
    body = rect(20, 90, 160, 140, f"url(#{gid})", r=14)
    hole = circle(100, 150, 12, "#3a2a1a") + rect(95, 154, 10, 30, "#3a2a1a")
    return svg(200, 234, shackle, body, hole, defs=defs)


@decoy("light bulb", "hardware", 0.11)
def light_bulb():
    glass = path("M100,10 C40,10 10,60 20,110 C30,150 60,160 64,200 L136,200 C140,160 170,150 180,110 "
                 "C190,60 160,10 100,10 Z", "#f7ec9a")
    base = "".join(rect(64, 200 + i * 14, 72, 12, "#b8bcc2", r=4) for i in range(3)) + \
        path("M80,242 L120,242 L108,262 L92,262 Z", "#3a3a3e")
    filament = stroke("M80,130 L90,100 L100,130 L110,100 L120,130", "#e0a526", 4)
    return svg(200, 264, glass, filament, base, gloss(50, 50, 14, 60, 0.5))


@decoy("paintbrush", "art supplies", 0.25)
def paintbrush():
    handle = path("M10,46 Q10,36 30,36 L250,30 L250,70 L30,64 Q10,64 10,54 Z", "#d62828")
    ferrule = rect(248, 26, 50, 48, "#c4c8cd")
    bristles = path("M296,28 Q360,30 380,50 Q360,70 296,72 Z", "#3a2a1a") + path("M350,40 Q376,46 380,50 "
                                                                                    "Q376,54 350,60 Z", "#2f6db5")
    return svg(390, 100, handle, ferrule, bristles)


@decoy("paint palette", "art supplies", 0.3)
def paint_palette():
    wood = "#d9b27a"
    board = path("M150,10 Q290,10 290,110 Q290,190 180,190 Q120,190 110,160 Q100,130 70,150 Q30,170 14,120 "
                 "Q0,10 150,10 Z", wood)
    hole = ellipse(70, 100, 18, 14, "#ffffff")
    blobs = "".join(circle(x, y, 16, c) for x, y, c in ((120, 50, "#d62828"), (180, 40, "#f2c12e"),
                                                       (240, 70, "#2f6db5"), (250, 130, "#3a8f3a"),
                                                       (200, 160, "#f2f2ee")))
    return svg(300, 200, board, hole, blobs)


@decoy("pencil", "stationery", 0.19)
def pencil():
    body = rect(40, 20, 300, 40, "#f2c12e") + rect(40, 20, 300, 12, mix("#f2c12e", 0.3)) + rect(40, 48, 300, 12,
                                                                                               "#d9a420")
    tip = poly([(340, 20), (400, 40), (340, 60)], "#e8c99a") + poly([(384, 34), (400, 40), (384, 46)], "#2a2a2e")
    eraser = rect(4, 20, 26, 40, "#e98a9a", r=6) + rect(26, 18, 18, 44, "#c4c8cd")
    return svg(404, 80, body, tip, eraser)


@decoy("scissors", "stationery", 0.2)
def scissors():
    blades = poly([(100, 120), (110, 120), (60, 0), (52, 6)], "#c4c8cd") + poly([(100, 120), (110, 120),
                                                                                (150, 6), (142, 0)], "#b0b4b9")
    rings = (ellipse(70, 170, 34, 40, "none", 'stroke="#d62828" stroke-width="16"')
             + ellipse(140, 170, 34, 40, "none", 'stroke="#d62828" stroke-width="16"'))
    return svg(210, 220, blades, rings, circle(105, 120, 6, "#55595e"))


@decoy("stapler", "stationery", 0.17)
def stapler():
    base = rect(10, 100, 300, 30, "#2a2a2e", r=10)
    top = path("M30,100 L30,60 Q30,30 70,30 L290,40 Q310,44 310,64 L310,96 Z", "#c81d25")
    hi = rect(60, 40, 220, 10, mix("#c81d25", 0.3), r=5)
    return svg(320, 134, base, top, hi)


@decoy("calculator", "stationery", 0.15)
def calculator():
    body = rect(10, 10, 160, 240, "#3a3d42", r=14)
    screen = rect(26, 26, 128, 50, "#b7c9a8", r=4) + text(146, 64, "128", 30, "#2a2a2e", anchor="end")
    keys = "".join(rect(26 + c * 34, 92 + r * 38, 26, 28, "#f2f2ee" if c < 3 else "#f08a24", r=5)
                   for r in range(4) for c in range(4))
    return svg(180, 260, body, screen, keys)


# ---- paper and books -------------------------------------------------------------------

@decoy("book", "paper", 0.24)
def book():
    green = "#2e6b4a"
    pages = poly([(30, 30), (230, 10), (250, 20), (50, 40)], "#f4f1e6")
    cover = rect(10, 30, 220, 280, green, r=4) + rect(10, 30, 26, 280, mix(green, -0.2))
    title = rect(60, 80, 140, 50, "#e0c27a", r=3) + rect(80, 250, 100, 8, "#e0c27a")
    side = poly([(230, 30), (250, 20), (250, 300), (230, 310)], "#f4f1e6")
    return svg(260, 314, pages, side, cover, title)


@decoy("envelope", "paper", 0.22)
def envelope():
    paper = "#f2ead6"
    return svg(300, 200, rect(10, 10, 280, 180, paper, r=4),
               poly([(10, 10), (150, 110), (290, 10)], mix(paper, -0.1)),
               poly([(10, 190), (130, 96), (170, 96), (290, 190)], mix(paper, -0.04)),
               rect(220, 30, 46, 54, "#d62828", r=2))


@decoy("notebook", "paper", 0.21)
def notebook():
    cover = rect(30, 10, 210, 290, "#2f6db5", r=8)
    rings = "".join(ellipse(30, 30 + i * 26, 14, 6, "none", 'stroke="#b8bcc2" stroke-width="5"') for i in range(11))
    label = rect(80, 50, 120, 40, "#f2f2ee", r=4)
    return svg(250, 310, cover, label, rings)


@decoy("newspaper", "paper", 0.4)
def newspaper():
    paper = "#ecebe4"
    page = rect(10, 10, 260, 320, paper) + poly([(270, 10), (290, 20), (290, 330), (270, 330)], mix(paper, -0.12))
    head = text(140, 56, "DAILY NEWS", 30, "#2a2a2e")
    lines = "".join(rect(24 + (i // 10) * 124, 110 + (i % 10) * 20, 110, 6, "#9a9a96") for i in range(20))
    photo = rect(24, 70, 232, 30, "#6b7a8a")
    return svg(300, 340, page, head, photo, lines)


# ---- clothing and accessories ----------------------------------------------------------

@decoy("baseball cap", "clothing", 0.28)
def baseball_cap():
    blue = "#1f4fa3"
    crown = path("M30,120 Q30,20 140,20 Q250,20 250,120 Z", blue)
    panels = stroke("M140,20 L140,120", mix(blue, -0.2), 4) + stroke("M140,20 Q90,60 80,120", mix(blue, -0.2), 4)
    brim = path("M200,110 Q300,110 330,140 Q260,150 200,136 Z", mix(blue, -0.2))
    return svg(340, 150, crown, panels, brim, circle(140, 22, 8, mix(blue, -0.3)))


@decoy("sunglasses", "clothing", 0.14)
def sunglasses():
    frame = "#2a2a2e"
    lenses = path("M20,30 L140,30 Q140,110 80,110 Q20,110 20,30 Z", frame) + \
        path("M180,30 L300,30 Q300,110 240,110 Q180,110 180,30 Z", frame)
    tint = ellipse(70, 58, 30, 18, "#5a6a7a", 'opacity="0.6"') + ellipse(230, 58, 30, 18, "#5a6a7a",
                                                                         'opacity="0.6"')
    bridge = stroke("M140,40 Q160,26 180,40", frame, 8)
    arms = rect(0, 28, 24, 8, frame, r=3) + rect(296, 28, 24, 8, frame, r=3)
    return svg(320, 120, arms, lenses, tint, bridge)


@decoy("scarf", "clothing", 1.4)
def scarf():
    red, cream = "#b8323a", "#efe4cf"
    body = path("M40,10 L120,10 L120,250 L40,250 Z", red) + path("M120,10 L200,10 L200,180 L120,180 Z",
                                                                  mix(red, -0.12))
    stripes = "".join(rect(40, 60 + i * 50, 80, 12, cream) for i in range(4)) + \
        "".join(rect(120, 40 + i * 50, 80, 12, mix(cream, -0.1)) for i in range(3))
    fringe = "".join(rect(42 + i * 10, 250, 4, 26, red) for i in range(8)) + \
        "".join(rect(122 + i * 10, 180, 4, 26, mix(red, -0.12)) for i in range(8))
    return svg(240, 280, body, stripes, fringe)


@decoy("sock", "clothing", 0.25)
def sock():
    grey = "#8e9aa6"
    body = path("M40,10 L120,10 L120,170 Q120,200 160,210 L210,220 Q240,230 230,260 Q220,290 180,286 "
                "L80,270 Q40,264 40,220 Z", grey)
    cuff = rect(40, 10, 80, 36, mix(grey, -0.2)) + "".join(rect(48 + i * 14, 14, 4, 28, mix(grey, -0.35))
                                                             for i in range(5))
    heel_toe = path("M40,220 Q40,264 80,270 L84,240 Q60,236 60,210 Z", "#c8242c") + \
        path("M200,216 L210,220 Q240,230 230,260 Q222,284 192,286 Q210,250 200,216 Z", "#c8242c")
    return svg(250, 292, body, cuff, heel_toe)


@decoy("mitten", "clothing", 0.25)
def mitten():
    teal = "#2a9d8f"
    body = path("M60,40 Q60,0 110,0 Q160,0 160,40 L160,200 L60,200 Z", teal)
    thumb = path("M60,110 Q20,100 14,70 Q10,46 30,44 Q50,44 60,80 Z", mix(teal, -0.12))
    cuff = rect(54, 190, 112, 50, "#f2f2ee", r=8)
    snow = "".join(circle(90 + (i % 2) * 40, 60 + i * 30, 6, "#f2f2ee") for i in range(4))
    return svg(180, 244, thumb, body, snow, cuff)


@decoy("wristwatch", "clothing", 0.22)
def wristwatch():
    strap = rect(60, 0, 80, 300, "#7b4a26", r=10)
    case = circle(100, 150, 70, "#c4c8cd") + circle(100, 150, 58, "#f6f6f2")
    ticks = "".join(rect(98, 96, 4, 10, "#2a2a2e", extra=f'transform="rotate({k * 30} 100 150)"') for k in range(12))
    hands = stroke("M100,150 L100,108", "#2a2a2e", 5) + stroke("M100,150 L132,160", "#2a2a2e", 4)
    return svg(200, 300, strap, case, ticks, hands, rect(168, 142, 12, 16, "#9ea3a8", r=2))


@decoy("backpack", "container", 0.45)
def backpack():
    orange = "#e76f51"
    body = rect(20, 40, 200, 260, orange, r=50)
    pocket = rect(50, 170, 140, 110, mix(orange, -0.12), r=24) + rect(60, 190, 120, 6, "#2a2a2e", r=3)
    handle = stroke("M90,44 Q90,6 120,6 Q150,6 150,44", "#2a2a2e", 10)
    zip_ = stroke("M50,110 Q120,80 190,110", "#2a2a2e", 5)
    return svg(240, 304, handle, body, pocket, zip_)


@decoy("suitcase", "container", 0.7)
def suitcase():
    blue = "#264653"
    body = rect(10, 60, 240, 300, blue, r=20) + "".join(rect(40 + i * 60, 70, 10, 280, mix(blue, 0.12), r=4)
                                                        for i in range(4))
    handle = path("M90,60 L90,20 L170,20 L170,60 L156,60 L156,34 L104,34 L104,60 Z", "#2a2a2e")
    wheels = circle(44, 364, 12, "#2a2a2e") + circle(216, 364, 12, "#2a2a2e")
    return svg(260, 378, handle, body, wheels)


@decoy("umbrella", "accessory", 0.9)
def umbrella():
    canopy = path("M10,150 Q20,20 170,20 Q320,20 330,150 Q300,130 270,150 Q240,130 210,150 Q190,130 170,150 "
                  "Q150,130 130,150 Q100,130 70,150 Q40,130 10,150 Z", "#5b3fa6")
    ribs = "".join(stroke(f"M170,22 Q{170 + d * 0.6},80 {170 + d},148", mix("#5b3fa6", -0.25), 3)
                   for d in (-100, -40, 40, 100))
    shaft = rect(166, 20, 8, 250, "#3a3a3e") + stroke("M170,266 Q170,300 142,300 Q122,300 122,280", "#7b4a26", 12)
    return svg(340, 310, shaft, canopy, ribs)


@decoy("handbag", "accessory", 0.3)
def handbag():
    tan = "#b5764a"
    handle = stroke("M70,110 Q70,10 150,10 Q230,10 230,110", mix(tan, -0.2), 14)
    body = path("M30,100 L270,100 L290,280 Q290,296 274,296 L26,296 Q10,296 10,280 Z", tan)
    flap = path("M30,100 L270,100 L262,170 Q150,200 38,170 Z", mix(tan, -0.1))
    clasp = rect(138, 168, 24, 20, "#c9a227", r=4)
    return svg(300, 300, handle, body, flap, clasp)


# ---- footwear --------------------------------------------------------------------------

@decoy("rain boot", "footwear", 0.38)
def rain_boot():
    yellow = "#f2c12e"
    boot = path("M40,10 L150,10 L150,240 Q220,240 250,270 Q260,300 240,310 L40,310 Z", yellow)
    sole = rect(36, 300, 216, 16, "#2a2a2e", r=6)
    top = rect(36, 6, 118, 24, mix(yellow, -0.15), r=4)
    return svg(260, 320, boot, top, sole, gloss(56, 40, 14, 190, 0.35))


@decoy("sneaker", "footwear", 0.29)
def sneaker():
    white, blue = "#f4f4f2", "#2f6db5"
    upper = path("M20,170 L20,80 Q30,50 70,50 L120,60 Q160,90 220,110 Q290,120 300,160 L300,170 Z", white)
    swoosh = path("M60,140 Q160,150 260,110 Q170,170 60,140 Z", blue)
    sole = rect(14, 166, 292, 26, mix(white, -0.15), r=10) + rect(14, 184, 292, 10, "#c4c8cd", r=4)
    laces = "".join(stroke(f"M{120 + i * 18},{70 + i * 8} L{136 + i * 18},{60 + i * 8}", "#9ea3a8", 4)
                    for i in range(4))
    return svg(320, 198, upper, swoosh, laces, sole)


@decoy("slipper", "footwear", 0.27)
def slipper():
    pink = "#e98aa0"
    sole = path("M20,120 Q10,60 60,50 L240,40 Q300,40 300,90 Q300,130 250,130 L60,140 Q24,140 20,120 Z",
                mix(pink, -0.25))
    upper = path("M140,40 L240,30 Q300,30 300,84 Q260,120 160,110 Q130,80 140,40 Z", pink)
    fluff = "".join(circle(150 + i * 22, 44 + (i % 2) * 6, 12, "#f6d6de") for i in range(6))
    return svg(310, 150, sole, upper, fluff)


# ---- electronics -----------------------------------------------------------------------

@decoy("headphones", "electronics", 0.2)
def headphones():
    band_ = stroke("M40,150 Q40,20 150,20 Q260,20 260,150", "#2a2a2e", 18)
    cups = rect(14, 130, 60, 100, "#2a2a2e", r=24) + rect(226, 130, 60, 100, "#2a2a2e", r=24)
    pads = rect(60, 140, 20, 80, "#c81d25", r=8) + rect(220, 140, 20, 80, "#c81d25", r=8)
    return svg(300, 240, band_, pads, cups)


@decoy("camera", "electronics", 0.13)
def camera():
    body = rect(10, 50, 280, 170, "#2a2a2e", r=16) + rect(10, 50, 280, 40, "#3a3a3e", r=16)
    top = rect(50, 26, 70, 30, "#2a2a2e", r=6) + rect(220, 34, 40, 18, "#c4c8cd", r=4)
    lens = circle(150, 140, 64, "#55595e") + circle(150, 140, 46, "#1a1a1e") + circle(136, 126, 12, "#6b7a9a")
    return svg(300, 230, body, top, lens, rect(30, 70, 30, 14, "#f6e27a", r=3))


@decoy("radio", "electronics", 0.3)
def radio():
    teal = "#3e8e8a"
    body = rect(10, 60, 300, 170, teal, r=22)
    handle = stroke("M60,62 L60,20 L260,20 L260,62", "#2a2a2e", 10)
    speaker = circle(100, 145, 56, "#efe4cf") + "".join(circle(100 + dx, 145 + dy, 4, "#9a8f7a")
                                                       for dx in (-30, -15, 0, 15, 30) for dy in (-30, -15, 0, 15, 30)
                                                       if dx * dx + dy * dy < 1100)
    dial = rect(180, 100, 110, 36, "#efe4cf", r=6) + rect(220, 102, 4, 32, "#c81d25")
    knobs = circle(200, 180, 16, "#2a2a2e") + circle(260, 180, 16, "#2a2a2e")
    return svg(320, 236, handle, body, speaker, dial, knobs)


@decoy("alarm clock", "electronics", 0.15)
def alarm_clock():
    red = "#c81d25"
    bells = circle(50, 50, 34, "#c9a227") + circle(190, 50, 34, "#c9a227")
    legs = stroke("M60,200 L40,240", "#2a2a2e", 10) + stroke("M180,200 L200,240", "#2a2a2e", 10)
    face = circle(120, 140, 96, red) + circle(120, 140, 78, "#f6f6f2")
    hands = stroke("M120,140 L120,84", "#2a2a2e", 6) + stroke("M120,140 L160,160", "#2a2a2e", 5)
    return svg(240, 244, bells, legs, face, hands, circle(120, 140, 6, red))


@decoy("TV remote", "electronics", 0.2)
def tv_remote():
    body = rect(20, 10, 100, 340, "#2a2a2e", r=30)
    power = circle(70, 50, 14, "#c81d25")
    pad = circle(70, 130, 36, "#55595e") + circle(70, 130, 14, "#3a3a3e")
    keys = "".join(rect(36 + c * 26, 200 + r * 30, 18, 18, "#9ea3a8", r=4) for r in range(4) for c in range(3))
    return svg(140, 360, body, power, pad, keys)


@decoy("mobile phone", "electronics", 0.15)
def mobile_phone():
    return svg(160, 310, rect(10, 10, 140, 290, "#2a2a2e", r=22), rect(20, 40, 120, 220, "#4a6fa5", r=6),
               rect(20, 40, 120, 30, "#6b8fc5", r=6), "".join(rect(32 + (i % 3) * 36, 90 + (i // 3) * 40, 24, 24,
                                                                    "#f2f2ee", r=6) for i in range(9)),
               circle(80, 280, 10, "#55595e"), rect(60, 22, 40, 6, "#55595e", r=3))


@decoy("laptop", "electronics", 0.35)
def laptop():
    lid = rect(50, 10, 280, 180, "#9ea3a8", r=10) + rect(64, 24, 252, 152, "#2c4a6e", r=4)
    base = poly([(30, 196), (350, 196), (380, 230), (0, 230)], "#c4c8cd")
    keys = "".join(rect(60 + i * 26, 202, 20, 6, "#8a8f95", r=2) for i in range(10))
    return svg(380, 236, lid, base, keys, rect(160, 218, 60, 8, "#9ea3a8", r=3))


@decoy("desk fan", "appliance", 0.4)
def desk_fan():
    blue = "#4aa3df"
    cage = circle(130, 120, 110, "#e0e4e8") + circle(130, 120, 96, "#f6f6f2")
    blades = "".join(ellipse(130, 70, 24, 46, blue, f'transform="rotate({k * 120} 130 120)"') for k in range(3))
    grill = "".join(stroke(f"M130,10 L130,230", "#c4c8cd", 2, f'transform="rotate({k * 30} 130 120)"')
                    for k in range(6))
    stand = rect(118, 220, 24, 70, "#e0e4e8") + rect(60, 286, 140, 20, "#e0e4e8", r=8)
    return svg(260, 310, stand, cage, blades, grill, circle(130, 120, 18, mix(blue, -0.3)))


@decoy("clothes iron", "appliance", 0.28)
def clothes_iron():
    purple = "#7b4fb5"
    plate = path("M20,170 L300,170 Q260,120 160,110 L60,110 Q20,120 20,170 Z", "#c4c8cd")
    body = path("M30,150 L290,150 Q250,90 150,84 L70,84 Q30,90 30,150 Z", purple)
    handle = path("M80,90 L80,40 Q80,20 110,20 L240,20 Q260,20 250,50 L210,96 L190,90 L220,44 L104,44 L104,90 Z",
                  mix(purple, -0.1))
    return svg(320, 176, handle, plate, body, circle(110, 120, 10, "#f2f2ee"))


@decoy("hair dryer", "personal care", 0.25)
def hair_dryer():
    pink = "#e98aa0"
    barrel = rect(80, 20, 200, 90, pink, r=40) + ellipse(280, 65, 16, 44, mix(pink, -0.3))
    back = circle(90, 65, 56, pink) + "".join(rect(60 + i * 12, 30, 5, 70, mix(pink, -0.2), r=2) for i in range(5))
    handle = path("M110,90 L170,90 L150,260 Q148,270 136,270 L110,270 Q100,270 100,258 Z", mix(pink, -0.12))
    return svg(300, 274, handle, back, barrel, rect(124, 140, 16, 30, "#f2f2ee", r=4))


@decoy("toothpaste", "personal care", 0.19)
def toothpaste():
    white, blue = "#f2f2f2", "#2f6db5"
    tube = path("M20,40 L330,10 L330,110 L20,80 Z", white)
    label = path("M100,34 L290,16 L290,104 L100,86 Z", blue) + text(195, 70, "FRESH", 26, "#ffffff")
    cap = rect(0, 40, 28, 40, "#c81d25", r=4)
    crimp = rect(326, 6, 14, 108, mix(white, -0.15))
    return svg(344, 120, tube, label, crimp, cap)


@decoy("hairbrush", "personal care", 0.23)
def hairbrush():
    wood = "#b5764a"
    head = ellipse(90, 90, 80, 84, wood) + ellipse(90, 90, 64, 68, "#2a2a2e")
    bristles = "".join(circle(90 + dx, 90 + dy, 4, "#d9d2c4") for dx in range(-48, 50, 16)
                       for dy in range(-52, 54, 16) if (dx / 60) ** 2 + (dy / 64) ** 2 < 1)
    handle = rect(76, 160, 28, 170, wood, r=12)
    return svg(180, 334, handle, head, bristles)


@decoy("comb", "personal care", 0.18)
def comb():
    black = "#2a2a2e"
    spine = rect(10, 20, 340, 30, black, r=8)
    teeth = "".join(rect(18 + i * 11, 46, 6, 60 if i < 18 else 46, black, r=2) for i in range(30))
    return svg(360, 110, spine, teeth)


# ---- toys ------------------------------------------------------------------------------

@decoy("yo-yo", "toy", 0.06)
def yo_yo():
    red = "#d62828"
    return svg(200, 260, stroke("M100,100 L100,4", "#efe4cf", 3), circle(100, 160, 90, red),
               circle(100, 160, 60, mix(red, -0.2)), circle(100, 160, 16, "#f2f2ee"), _shade_ball(100, 160, 90, 0.14),
               gloss(46, 110, 14, 26, 0.4))


@decoy("teddy bear", "toy", 0.3)
def teddy_bear():
    brown = "#a0693a"
    ears = circle(60, 40, 30, brown) + circle(160, 40, 30, brown) + circle(60, 40, 14, "#d9a875") + circle(160, 40, 14,
                                                                                                          "#d9a875")
    head = circle(110, 90, 66, brown)
    face = ellipse(110, 116, 30, 22, "#d9a875") + circle(88, 80, 7, "#1a1a1a") + circle(132, 80, 7, "#1a1a1a") + \
        ellipse(110, 108, 10, 7, "#1a1a1a")
    body = ellipse(110, 220, 70, 76, brown) + ellipse(110, 230, 40, 46, "#d9a875")
    limbs = (ellipse(40, 200, 22, 36, brown) + ellipse(180, 200, 22, 36, brown)
             + ellipse(70, 290, 30, 22, brown) + ellipse(150, 290, 30, 22, brown))
    return svg(220, 314, limbs, body, ears, head, face)


@decoy("toy car", "toy", 0.1)
def toy_car():
    blue = "#2a7fd4"
    body = path("M10,110 L10,80 Q10,70 30,66 L90,60 L130,24 L240,24 L280,60 Q330,66 330,86 L330,110 Z", blue)
    windows = poly([(100, 62), (136, 32), (180, 32), (180, 62)], "#cfe8f2") + poly([(192, 32), (234, 32), (264, 62),
                                                                                  (192, 62)], "#cfe8f2")
    wheels = "".join(circle(x, 112, 28, "#2a2a2e") + circle(x, 112, 12, "#c4c8cd") for x in (80, 260))
    return svg(340, 144, body, windows, wheels, rect(300, 74, 20, 10, "#f6e27a", r=3))


@decoy("rubber duck", "toy", 0.1)
def rubber_duck():
    yellow = "#f6cf2a"
    body = path("M20,150 Q20,90 90,96 L170,100 Q240,100 236,150 Q230,210 130,210 Q20,210 20,150 Z", yellow)
    head = circle(80, 70, 52, yellow)
    beak = path("M20,74 Q0,80 4,92 Q20,98 40,88 Z", "#f08a24")
    wing = path("M110,130 Q170,110 200,140 Q160,170 110,150 Z", mix(yellow, -0.15))
    return svg(240, 214, body, head, beak, wing, circle(70, 60, 7, "#1a1a1a"), gloss(56, 30, 14, 20, 0.5))


@decoy("toy blocks", "toy", 0.15)
def toy_blocks():
    blocks = ""
    for x, y, c, letter in ((10, 120, "#d62828", "A"), (120, 120, "#2a7fd4", "B"), (64, 10, "#3a8f3a", "C")):
        blocks += rect(x, y, 104, 104, c, r=6) + rect(x + 16, y + 16, 72, 72, mix(c, 0.35), r=4) + \
            text(x + 52, y + 76, letter, 56, c)
    return svg(234, 234, blocks)


@decoy("kite", "toy", 0.9)
def kite():
    sails = (poly([(120, 0), (220, 120), (120, 120)], "#e63946") + poly([(120, 0), (20, 120), (120, 120)], "#f6c026")
             + poly([(20, 120), (120, 320), (120, 120)], "#2a7fd4") + poly([(220, 120), (120, 320), (120, 120)],
                                                                           "#3a8f3a"))
    tail = stroke("M120,320 Q150,360 120,400 Q90,440 130,470", "#2a2a2e", 3) + \
        "".join(poly([(120 + dx, y), (134 + dx, y + 8), (120 + dx, y + 16), (106 + dx, y + 8)], "#e63946")
                for dx, y in ((10, 350), (-8, 400), (10, 444)))
    return svg(240, 476, sails, stroke("M120,0 L120,320 M20,120 L220,120", "#5b3a1a", 3), tail)


# ---- instruments -----------------------------------------------------------------------

@decoy("violin", "instrument", 0.6)
def violin():
    wood = "#a0522d"
    body = path("M80,120 C30,120 20,170 40,200 C50,214 50,226 40,240 C10,280 30,340 100,340 C170,340 190,280 160,240 "
                "C150,226 150,214 160,200 C180,170 170,120 120,120 Z", wood)
    shade = path("M120,120 C170,120 180,170 160,200 C150,214 150,226 160,240 C190,280 170,340 100,340 "
                 "C150,320 160,280 140,240 C132,226 132,214 140,200 C156,170 150,130 120,120 Z", mix(wood, -0.25))
    neck = rect(92, 10, 16, 200, "#2a2a2e", r=4) + path("M90,10 Q90,-6 104,0 Q118,6 110,20 Z", "#5b3a1a")
    holes = stroke("M70,220 Q60,240 72,262", "#2a1a10", 4) + stroke("M130,220 Q140,240 128,262", "#2a1a10", 4)
    bridge = rect(80, 250, 40, 6, "#e0c27a")
    tail = path("M88,280 L112,280 L106,330 L94,330 Z", "#2a2a2e")
    strings = "".join(stroke(f"M{96 + i * 3},14 L{94 + i * 4},300", "#e8e8e8", 0.8) for i in range(4))
    return svg(200, 344, body, shade, neck, holes, tail, bridge, strings)


@decoy("snare drum", "instrument", 0.4)
def snare_drum():
    defs, shell = cylinder(10, 30, 280, 150, "#c81d25", top="#f4f1ea", cap=0.16)
    hoops = rect(10, 54, 280, 10, "#c4c8cd") + rect(10, 160, 280, 10, "#c4c8cd")
    lugs = "".join(rect(30 + i * 52, 70, 12, 86, "#c4c8cd", r=4) for i in range(5))
    sticks = stroke("M60,10 L170,60", "#e0c27a", 8) + stroke("M240,6 L130,64", "#e0c27a", 8)
    return svg(300, 190, shell, hoops, lugs, sticks, defs=defs)


@decoy("trumpet", "instrument", 0.5)
def trumpet():
    brass = "#d4a62a"
    bell = path("M300,40 Q380,30 400,0 L400,140 Q380,110 300,100 Z", brass) + ellipse(400, 70, 12, 70,
                                                                                       mix(brass, -0.3))
    tube = rect(30, 60, 280, 20, brass, r=8) + stroke("M90,80 L90,120 Q90,140 110,140 L240,140 Q260,140 260,120 "
                                                     "L260,80", brass, 16)
    valves = "".join(rect(140 + i * 34, 30, 18, 70, mix(brass, -0.12), r=4) + rect(136 + i * 34, 20, 26, 12,
                                                                                    "#f2f2ee", r=4)
                     for i in range(3))
    mouth = rect(0, 60, 36, 20, "#c4c8cd", r=6)
    return svg(412, 150, tube, bell, valves, mouth, gloss(40, 62, 240, 5, 0.4, r=2))


@decoy("harmonica", "instrument", 0.1)
def harmonica():
    steel = "#c4c8cd"
    gid, defs = band(steel, horizontal=False)
    return svg(320, 110, rect(10, 10, 300, 90, f"url(#{gid})", r=8), rect(20, 46, 280, 26, "#3a3a3e", r=3),
               "".join(rect(28 + i * 27, 50, 18, 18, "#1a1a1e", r=2) for i in range(10)), defs=defs)


@decoy("tambourine", "instrument", 0.25)
def tambourine():
    wood = "#d9a35a"
    rim = ellipse(150, 150, 140, 140, wood) + ellipse(150, 150, 120, 120, "#f4ead2")
    jingles = "".join(circle(150 + 130 * math.cos(math.radians(a)), 150 + 130 * math.sin(math.radians(a)), 14,
                             "#c4c8cd") for a in range(0, 360, 60))
    return svg(300, 300, rim, jingles, gloss(90, 70, 40, 10, 0.4))


# ---- decor, optics, music, garden ------------------------------------------------------

@decoy("desk globe", "decor", 0.4)
def desk_globe():
    sea = "#3a7fc4"
    land = (path("M60,70 Q90,40 120,60 Q130,90 100,110 Q70,120 60,70 Z", "#5aa651")
            + path("M140,120 Q170,110 180,140 Q170,180 140,170 Q126,150 140,120 Z", "#5aa651"))
    ball = circle(120, 120, 96, sea) + land + _shade_ball(120, 120, 96, 0.16)
    arm = stroke("M210,140 A100,100 0 0 1 60,210", "#c9a227", 8)
    stand = rect(110, 216, 20, 50, "#5b3a1a") + rect(60, 262, 120, 20, "#5b3a1a", r=6)
    return svg(240, 284, stand, ball, arm, gloss(66, 64, 16, 30, 0.35))


@decoy("trophy", "decor", 0.3)
def trophy():
    gold = "#d4a62a"
    gid, defs = band(gold)
    cup = path("M50,20 L190,20 Q190,140 120,150 Q50,140 50,20 Z", f"url(#{gid})")
    handles = stroke("M52,40 Q10,40 14,80 Q20,110 60,110", gold, 10) + stroke("M188,40 Q230,40 226,80 Q220,110 180,110",
                                                                            gold, 10)
    stem = rect(108, 148, 24, 50, gold) + rect(70, 196, 100, 20, gold, r=4) + rect(60, 214, 120, 50, "#3a2a1a", r=4)
    plate = rect(84, 228, 72, 22, "#e0c27a", r=3)
    return svg(240, 266, handles, cup, stem, plate, defs=defs)


@decoy("candle", "decor", 0.2)
def candle():
    defs, wax = cylinder(30, 80, 100, 220, "#f2e6c8", top="#e6d6ae", cap=0.16)
    flame = path("M80,10 Q100,50 92,70 Q80,84 68,70 Q60,50 80,10 Z", "#f6a623") + ellipse(80, 62, 7, 12, "#f6e27a")
    return svg(160, 304, wax, stroke("M80,92 L80,72", "#2a2a2e", 3), flame, defs=defs)


@decoy("table lamp", "decor", 0.45)
def table_lamp():
    shade = poly([(60, 10), (200, 10), (240, 140), (20, 140)], "#e9c46a") + poly([(160, 10), (200, 10), (240, 140),
                                                                                (190, 140)], "#d4ac4c")
    pole = rect(122, 140, 16, 130, "#5b3a1a")
    base = ellipse(130, 280, 70, 18, "#5b3a1a")
    return svg(260, 300, pole, base, shade)


@decoy("wall clock", "decor", 0.3)
def wall_clock():
    face = circle(150, 150, 140, "#2a2a2e") + circle(150, 150, 122, "#f6f6f2")
    numerals = "".join(rect(146, 36, 8, 20, "#2a2a2e", extra=f'transform="rotate({k * 30} 150 150)"') for k in range(12))
    hands = stroke("M150,150 L150,70", "#2a2a2e", 8) + stroke("M150,150 L210,170", "#2a2a2e", 6) + \
        stroke("M150,150 L100,230", "#c81d25", 3)
    return svg(300, 300, face, numerals, hands, circle(150, 150, 8, "#2a2a2e"))


@decoy("binoculars", "optics", 0.15)
def binoculars():
    black = "#2a2a2e"
    tubes = rect(20, 60, 100, 150, black, r=20) + rect(160, 60, 100, 150, black, r=20)
    eyes = rect(36, 20, 68, 50, "#3a3a3e", r=10) + rect(176, 20, 68, 50, "#3a3a3e", r=10)
    lenses = ellipse(70, 206, 44, 12, "#5a6f8a") + ellipse(210, 206, 44, 12, "#5a6f8a")
    bridge = rect(116, 80, 48, 40, "#3a3a3e", r=6) + circle(140, 70, 16, "#55595e")
    return svg(280, 222, tubes, eyes, bridge, lenses, gloss(34, 80, 10, 100, 0.2))


@decoy("magnifying glass", "optics", 0.25)
def magnifying_glass():
    rim = circle(110, 110, 100, "#2a2a2e") + circle(110, 110, 84, "#cfe8f2")
    handle = rect(178, 178, 40, 150, "#7b4a26", r=14, extra='transform="rotate(-45 198 253)"')
    return svg(330, 330, handle, rim, gloss(60, 60, 20, 60, 0.6, r=10))


@decoy("cassette tape", "music", 0.1)
def cassette_tape():
    body = rect(10, 10, 300, 190, "#2a2a2e", r=10)
    label = rect(30, 30, 260, 100, "#f2c12e", r=6) + rect(30, 60, 260, 10, "#e76f51")
    window = rect(100, 80, 120, 40, "#55595e", r=6) + circle(124, 100, 14, "#f2f2ee") + circle(196, 100, 14, "#f2f2ee")
    bottom = poly([(70, 200), (90, 160), (230, 160), (250, 200)], "#3a3a3e")
    return svg(320, 210, body, label, window, bottom)


@decoy("compact disc", "music", 0.12)
def compact_disc():
    disc = circle(120, 120, 114, "#d8dde4")
    rainbow = path("M40,60 A100,100 0 0 1 120,20 L120,60 A60,60 0 0 0 72,86 Z", "#c9b6e8", 'opacity="0.8"') + \
        path("M200,180 A100,100 0 0 1 120,220 L120,180 A60,60 0 0 0 168,154 Z", "#b6e8d6", 'opacity="0.8"')
    hole = circle(120, 120, 30, "#b8bcc2") + circle(120, 120, 16, "#ffffff")
    return svg(240, 240, disc, rainbow, hole)


@decoy("garden trowel", "garden", 0.3)
def garden_trowel():
    blade = path("M200,40 Q300,40 340,80 Q300,120 200,120 Q180,80 200,40 Z", "#b8bcc2")
    shaft = rect(140, 72, 70, 16, "#9ea3a8")
    handle = rect(10, 60, 140, 40, "#3a8f3a", r=18)
    return svg(350, 160, handle, shaft, blade, gloss(220, 56, 80, 8, 0.4))


@decoy("gardening gloves", "garden", 0.25)
def garden_gloves():
    green = "#7fb069"
    glove = path("M40,300 L40,140 L30,70 Q30,56 42,56 Q54,56 56,70 L64,130 L66,40 Q66,26 80,26 Q94,26 94,40 "
                 "L96,120 L104,30 Q104,16 118,16 Q132,16 132,30 L128,124 L140,56 Q142,42 156,44 Q168,48 166,62 "
                 "L150,170 L170,140 Q184,124 196,136 Q204,148 190,166 L150,230 L150,300 Z", green)
    cuff = rect(36, 270, 118, 40, "#f08a24", r=6)
    return svg(210, 314, glove, cuff)
