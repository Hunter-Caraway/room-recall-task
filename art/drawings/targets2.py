"""Flat drawings of the remaining target objects (see targets.py)."""
from __future__ import annotations

import math

from .kit import band, circle, cylinder, ellipse, gloss, mix, path, poly, rect, stroke, svg, text
from .targets import drawing


def _ball(r, base):
    return circle(r, r, r, base)


def _ball_shade(r, opacity=0.18):
    return path(f"M{r},0 A{r},{r} 0 0 1 {r},{2 * r} A{r * 0.72},{r} 0 0 0 {r},0 Z", "#000000",
                f'opacity="{opacity}"')


@drawing
def _8ball():
    return svg(200, 200, _ball(100, "#151517"), circle(84, 72, 40, "#f7f7f2"), text(84, 88, "8", 46, "#151517"),
               _ball_shade(100, 0.3), gloss(40, 36, 18, 34, 0.35))


@drawing
def volleyball():
    stripes = (path("M30,40 C80,70 110,120 110,196 L140,190 C140,110 110,60 60,22 Z", "#c8242c")
               + path("M150,20 C120,80 130,140 186,170 L196,140 C150,120 150,80 176,36 Z", "#c8242c"))
    seams = stroke("M60,22 C110,60 140,110 140,190", "#d8d2c4", 3) + stroke("M176,36 C150,80 150,120 196,140",
                                                                          "#d8d2c4", 3)
    return svg(200, 200, f'<clipPath id="vb"><circle cx="100" cy="100" r="100"/></clipPath>',
               _ball(100, "#f1ece0"), f'<g clip-path="url(#vb)">{stripes}{seams}</g>', _ball_shade(100),
               gloss(42, 34, 18, 34, 0.45))


@drawing
def football():
    brown = "#7b3d1e"
    body = ellipse(150, 80, 146, 76, brown)
    shade = path("M150,4 C240,4 296,50 296,80 C296,110 240,156 150,156 C230,140 270,110 270,80 C270,50 230,20 150,4 Z",
                 mix(brown, -0.35))
    stripes = rect(28, 30, 14, 100, "#f2efe6", r=6, extra='transform="rotate(-12 35 80)"') + \
        rect(258, 30, 14, 100, "#f2efe6", r=6, extra='transform="rotate(12 265 80)"')
    lace = rect(96, 22, 108, 8, "#f2efe6", r=4) + "".join(rect(102 + i * 12, 14, 5, 24, "#f2efe6", r=2) for i in range(8))
    return svg(300, 160, body, shade, stripes, lace, gloss(70, 40, 60, 12, 0.25))


@drawing
def bolt01a():
    zinc, dark = "#c9b25a", "#8c7a2e"
    head = poly([(0, 30), (20, 6), (60, 6), (60, 94), (20, 94), (0, 70)], zinc) + \
        poly([(20, 6), (60, 6), (60, 94), (20, 94)], mix(zinc, -0.12)) + rect(22, 6, 6, 88, mix(zinc, 0.3))
    shank = rect(58, 22, 182, 56, mix(zinc, -0.05), r=6)
    threads = "".join(stroke(f"M{110 + i * 9},22 L{104 + i * 9},78", dark, 3) for i in range(14))
    return svg(244, 100, shank, threads, head, gloss(64, 28, 170, 6, 0.4, r=3))


@drawing
def bowtie():
    knit = "#4a4552"
    left = path("M10,20 C40,10 80,40 100,50 C80,60 40,90 10,80 C0,70 0,30 10,20 Z", knit)
    right = path("M190,20 C160,10 120,40 100,50 C120,60 160,90 190,80 C200,70 200,30 190,20 Z", mix(knit, -0.12))
    knot = rect(86, 34, 28, 32, mix(knit, 0.12), r=8)
    texture = "".join(stroke(f"M{x},28 L{x},72", "#5c5766", 1.4, 'opacity="0.6"') for x in range(20, 190, 7))
    return svg(200, 100, left, right, texture, knot)


@drawing
def coloringset():
    wood, inside = "#b0532c", "#efe4cf"
    lid = rect(10, 0, 300, 120, wood, r=6) + rect(22, 12, 276, 96, inside, r=3)
    colours = ["#d62828", "#f77f00", "#fcbf49", "#2a9d8f", "#264653", "#6a4c93", "#e76f51", "#43aa8b", "#277da1",
               "#f94144", "#90be6d", "#577590"]
    pencils = "".join(rect(30 + i * 22, 20, 12, 80, colours[i % len(colours)], r=2) for i in range(12))
    base = poly([(0, 126), (320, 126), (306, 190), (14, 190)], wood) + poly([(16, 132), (304, 132), (294, 176),
                                                                            (26, 176)], inside)
    pans = "".join(ellipse(48 + i * 30, 154, 11, 7, colours[(i + 3) % len(colours)]) for i in range(9))
    return svg(320, 192, lid, pencils, base, pans)


@drawing
def electricmixer():
    bronze, steel = "#a08463", "#c7cbd0"
    base = path("M20,250 Q20,232 40,232 L220,232 Q240,232 240,250 L240,262 L20,262 Z", bronze)
    column = path("M170,232 L190,110 L238,110 L232,232 Z", bronze)
    head = path("M40,60 Q40,20 90,20 L230,20 Q258,20 258,60 L258,104 Q258,124 236,124 L60,124 Q40,124 40,104 Z",
                bronze)
    head_hi = path("M50,40 Q60,28 90,28 L220,28 Q200,36 90,40 Z", "#ffffff", 'opacity="0.3"')
    bowl = path("M50,140 L170,140 L160,214 Q156,230 136,230 L84,230 Q64,230 60,214 Z", steel)
    bowl_hi = path("M62,146 L76,146 L84,222 L74,222 Z", "#ffffff", 'opacity="0.5"')
    rim = rect(44, 134, 132, 10, mix(steel, 0.1), r=4)
    beater = rect(102, 124, 8, 30, "#8a8d92")
    knob = circle(244, 70, 9, mix(bronze, -0.25))
    return svg(262, 264, column, base, bowl, bowl_hi, rim, beater, head, head_hi, knob)


@drawing
def electrictoothbrush01c():
    white, navy = "#f4f6f8", "#1f3a6b"
    handle = path("M10,30 Q10,8 34,8 L200,14 Q214,16 214,30 Q214,44 200,46 L34,52 Q10,52 10,30 Z", white)
    stripe = path("M40,12 L190,16 Q200,18 200,30 Q200,42 190,44 L40,48 Z", navy, 'opacity="0.9"')
    button = circle(110, 30, 7, "#e9eef5")
    neck = path("M214,24 L262,26 L262,34 L214,36 Z", white)
    head = rect(262, 18, 26, 24, white, r=8) + rect(266, 8, 18, 12, "#3a8de0", r=3) + rect(270, 4, 10, 6, "#ffffff",
                                                                                             r=2)
    shade = path("M10,30 Q10,52 34,52 L200,46 Q214,44 214,30 Z", "#000000", 'opacity="0.08"')
    return svg(292, 56, handle, stripe, button, neck, head, shade)


@drawing
def flipflop01b():
    sole = ellipse(150, 56, 146, 44, "#1d1d1f")
    top = ellipse(150, 50, 136, 36, "#2b2b2e")
    flower = "".join(ellipse(220 + 14 * math.cos(math.radians(a)), 52 + 8 * math.sin(math.radians(a)), 8, 4,
                             "#f2f2ee", f'transform="rotate({a} {220 + 14 * math.cos(math.radians(a))} '
                                        f'{52 + 8 * math.sin(math.radians(a))})"') for a in range(0, 360, 45))
    straps = stroke("M58,24 C90,40 110,48 120,50 M58,78 C90,62 110,54 120,50", "#d1232a", 12)
    post = circle(60, 50, 7, "#d1232a")
    return svg(300, 104, sole, top, flower, circle(220, 52, 6, "#f5c518"), straps, post)


@drawing
def gamecontroller01():
    """Grey three-prong console controller, from above."""
    grey = "#aeb0b4"
    body = path("M40,30 Q150,0 260,30 Q296,44 290,90 L282,150 Q276,176 250,170 Q232,166 228,140 L214,104 "
                "L186,104 L176,170 Q166,196 150,196 Q134,196 124,170 L114,104 L86,104 L72,140 Q68,166 50,170 "
                "Q24,176 18,150 L10,90 Q4,44 40,30 Z", grey)
    shade = path("M150,104 L176,170 Q166,196 150,196 Z", mix(grey, -0.15)) + \
        path("M228,104 L250,170 Q276,176 282,150 L290,90 Q280,120 228,104 Z", mix(grey, -0.12))
    dpad = rect(36, 56, 44, 14, "#3a3a3e", r=2) + rect(51, 41, 14, 44, "#3a3a3e", r=2)
    c_buttons = circle(240, 44, 7, "#f2c12e") + circle(256, 58, 7, "#f2c12e") + circle(224, 58, 7, "#f2c12e") + \
        circle(240, 72, 7, "#f2c12e")
    a_b = circle(212, 84, 9, "#2f62c9") + circle(196, 68, 9, "#2a9d4a")
    start = circle(150, 60, 7, "#c8302b")
    stick = circle(150, 122, 14, "#6e7076") + circle(150, 122, 7, "#8a8c92")
    cable = stroke("M150,8 C150,-6 120,-6 108,4", "#6e7076", 6)
    return svg(300, 200, body, shade, dpad, c_buttons, a_b, start, stick)


@drawing
def garbagecan02():
    steel = "#b9bdc3"
    defs, body = cylinder(10, 30, 180, 250, steel, top=mix(steel, 0.15), cap=0.1)
    lid = path("M8,48 Q8,14 100,10 Q192,14 192,48 Z", mix(steel, 0.12)) + rect(6, 44, 188, 10, "#2a2a2c", r=4)
    pedal = rect(80, 266, 44, 14, "#2a2a2c", r=4)
    base = rect(10, 262, 180, 12, "#2a2a2c", r=4)
    return svg(200, 284, body, lid, base, pedal, gloss(30, 70, 10, 180, 0.4), defs=defs)


@drawing
def handheldtelescope():
    brass, dark = "#b8763c", "#6d4220"
    parts = [rect(0, 20, 140, 56, brass, r=6), rect(132, 26, 110, 44, mix(brass, 0.08), r=5),
             rect(234, 32, 90, 32, mix(brass, 0.15), r=4), rect(316, 38, 70, 20, mix(brass, 0.2), r=3)]
    rings = rect(0, 16, 22, 64, dark, r=6) + rect(126, 22, 12, 52, dark, r=3) + rect(230, 28, 10, 40, dark, r=3) + \
        rect(312, 34, 8, 28, dark, r=2) + rect(380, 34, 14, 28, "#3a3a3a", r=4)
    shade = rect(0, 54, 386, 20, "#000000", r=4, extra='opacity="0.12"')
    return svg(396, 96, *parts, rings, shade, gloss(30, 26, 90, 6, 0.35, r=3))


@drawing
def ipod():
    slab = path("M10,60 L190,10 L250,40 L70,92 Z", "#16161a")
    edge = path("M10,60 L70,92 L70,98 L10,66 Z", "#5a5c62") + path("M70,92 L250,40 L250,46 L70,98 Z", "#3c3d42")
    screen = path("M40,58 L176,20 L222,42 L86,82 Z", "#2c3a4c")
    glare = path("M60,56 L120,40 L140,50 L80,66 Z", "#ffffff", 'opacity="0.12"')
    return svg(260, 100, slab, edge, screen, glare)


@drawing
def jarofapplesauce():
    glass = "#d6c66a"
    defs, jar = cylinder(10, 44, 160, 186, glass, top=mix(glass, 0.1), cap=0.1)
    lid = rect(18, 6, 144, 46, "#1f5a3a", r=10) + rect(18, 40, 144, 10, mix("#1f5a3a", -0.3), r=3)
    label = rect(10, 130, 160, 70, "#dfe7c9") + circle(36, 165, 14, "#c8302b")
    return svg(180, 236, jar, label, lid, gloss(26, 70, 9, 140, 0.5), defs=defs)


@drawing
def jeans01():
    denim = "#3d5a86"
    waist = rect(20, 0, 160, 40, mix(denim, -0.1), r=4)
    legs = path("M20,36 L180,36 L176,390 L116,390 L104,120 L96,120 L84,390 L24,390 Z", denim)
    seams = stroke("M100,40 L100,118", "#c9a24a", 2) + stroke("M46,80 Q60,96 92,96 M154,80 Q140,96 108,96",
                                                                "#c9a24a", 2)
    fade = path("M40,140 L70,140 L76,330 L46,330 Z", "#ffffff", 'opacity="0.12"') + \
        path("M130,140 L160,140 L156,330 L126,330 Z", "#ffffff", 'opacity="0.12"')
    loops = "".join(rect(x, 0, 8, 18, mix(denim, -0.25), r=2) for x in (36, 70, 124, 156))
    button = circle(100, 20, 6, "#c9a24a")
    return svg(200, 392, legs, fade, waist, loops, seams, button)


@drawing
def knife03():
    blade = path("M0,40 L200,24 L200,56 Q100,58 0,40 Z", "#d4d8dd")
    edge = path("M0,40 Q100,58 200,56 L200,50 Q100,52 0,40 Z", "#9aa0a8")
    handle = rect(196, 22, 110, 36, "#1c1c1e", r=10) + "".join(circle(222 + i * 30, 40, 4, "#c0c4ca") for i in range(3))
    return svg(310, 70, blade, edge, handle, gloss(60, 32, 120, 4, 0.6, r=2))


@drawing
def laundrybasket01a():
    green = "#3fbf8f"
    body = path("M10,20 L310,20 L280,170 Q278,180 266,180 L54,180 Q42,180 40,170 Z", green)
    rim = rect(0, 10, 320, 22, mix(green, 0.12), r=8)
    holes = "".join(rect(54 + c * 30, 50 + r_ * 34, 18, 24, mix(green, -0.3), r=4) for c in range(8) for r_ in range(3))
    handle = rect(130, 14, 60, 10, mix(green, -0.35), r=5)
    return svg(320, 182, body, holes, rim, handle)


@drawing
def lintroller():
    roller = rect(0, 10, 120, 70, "#f4f4f2", r=10) + rect(0, 10, 120, 12, "#ffffff", r=6) + \
        rect(0, 62, 120, 18, "#d6d6d2", r=6)
    end = ellipse(120, 45, 10, 35, "#c9c9c4")
    handle = path("M126,40 L250,30 Q262,30 262,42 Q262,54 250,54 L126,50 Z", "#3a3c40")
    grip = rect(200, 30, 50, 24, "#26272a", r=10)
    return svg(264, 90, roller, end, handle, grip)


@drawing
def musicsheet():
    paper = poly([(20, 0), (300, 0), (320, 120), (0, 120)], "#fbfbf8")
    shadow_edge = poly([(0, 120), (320, 120), (320, 124), (0, 124)], "#d8d8d2")
    staves = ""
    for k in range(3):
        y0 = 22 + k * 32
        staves += "".join(stroke(f"M{30 - y0 * 0.1},{y0 + i * 4} L{292 + y0 * 0.1},{y0 + i * 4}", "#6a6a6a", 0.9)
                          for i in range(5))
        staves += "".join(ellipse(50 + j * 26, y0 + (j * 3) % 16, 4, 3, "#2a2a2a") for j in range(10))
    return svg(320, 126, paper, shadow_edge, staves)


@drawing
def painting():
    frame = rect(0, 0, 200, 250, "#3e2b1f", r=4) + rect(10, 10, 180, 230, "#6b4a2f", r=2)
    canvas = rect(22, 22, 156, 206, "#8c7a52")
    petals = "".join(ellipse(100 + 30 * math.cos(math.radians(a)), 110 + 30 * math.sin(math.radians(a)), 26, 14,
                             "#c9b48a", f'transform="rotate({a} {100 + 30 * math.cos(math.radians(a))} '
                                        f'{110 + 30 * math.sin(math.radians(a))})" opacity="0.9"')
                     for a in range(0, 360, 60))
    stem = stroke("M100,140 C96,170 110,200 98,226", "#5b6b3a", 6) + ellipse(80, 190, 18, 8, "#6d7d45")
    return svg(200, 250, frame, canvas, petals, circle(100, 110, 14, "#d9a441"), stem)


@drawing
def record():
    disc = circle(100, 100, 100, "#121214")
    grooves = "".join(circle(100, 100, r, "none", 'stroke="#2a2a2e" stroke-width="1.2"') for r in range(44, 98, 6))
    label = circle(100, 100, 36, "#d6874a") + circle(100, 100, 3, "#121214")
    shine = path("M30,40 A100,100 0 0 1 80,4 L90,30 A72,72 0 0 0 50,56 Z", "#ffffff", 'opacity="0.12"')
    return svg(200, 200, disc, grooves, label, shine)


@drawing
def rubikcube():
    top = [(100, 0), (190, 40), (100, 80), (10, 40)]
    left = [(10, 40), (100, 80), (100, 190), (10, 150)]
    right = [(100, 80), (190, 40), (190, 150), (100, 190)]
    out = poly(top, "#1a1a1a") + poly(left, "#1a1a1a") + poly(right, "#1a1a1a")
    colours = {"top": ["#f5f5f0", "#f2c12e", "#f5f5f0", "#2a9d4a", "#f5f5f0", "#c8302b", "#f2c12e", "#2f62c9",
                       "#f5f5f0"],
               "left": ["#c8302b", "#2f62c9", "#f2c12e", "#2a9d4a", "#c8302b", "#f28c28", "#2f62c9", "#c8302b",
                        "#2a9d4a"],
               "right": ["#2a9d4a", "#f28c28", "#2a9d4a", "#f2c12e", "#2a9d4a", "#2f62c9", "#c8302b", "#f28c28",
                         "#2a9d4a"]}

    def face(o, u, v, cols, shade):
        tiles = ""
        for i in range(3):
            for j in range(3):
                pts = []
                for a, b in ((i + 0.1, j + 0.1), (i + 0.9, j + 0.1), (i + 0.9, j + 0.9), (i + 0.1, j + 0.9)):
                    pts.append((o[0] + u[0] * a / 3 + v[0] * b / 3, o[1] + u[1] * a / 3 + v[1] * b / 3))
                tiles += poly(pts, mix(cols[i * 3 + j], shade))
        return tiles
    out += face((10, 40), (90, -40), (90, 40), colours["top"], 0.0)
    out += face((10, 40), (90, 40), (0, 110), colours["left"], -0.1)
    out += face((100, 80), (90, -40), (0, 110), colours["right"], -0.22)
    return svg(200, 192, out)


@drawing
def saltshaker03a():
    glass = "#eef0f2"
    body = path("M14,70 L106,70 L106,214 Q106,224 96,224 L24,224 Q14,224 14,214 Z", glass)
    salt = rect(16, 110, 88, 112, "#ffffff", r=6)
    shade = rect(78, 70, 28, 154, "#000000", r=4, extra='opacity="0.08"')
    cap = path("M10,72 L18,24 Q60,4 102,24 L110,72 Z", "#b9bdc3") + rect(10, 64, 100, 10, "#9ea3a9", r=3)
    holes = "".join(circle(36 + i * 16, 38 + (i % 2) * 10, 3.5, "#5b5f66") for i in range(4))
    return svg(120, 226, body, salt, shade, cap, holes, gloss(24, 84, 7, 120, 0.5))


@drawing
def snowglobe():
    glass = circle(100, 90, 86, "#cfe5f2", 'opacity="0.9"')
    elf = (circle(100, 80, 26, "#f2c9a2") + path("M74,70 Q100,20 126,70 Z", "#2a9d4a") + circle(100, 26, 8, "#c8302b")
           + path("M70,104 L130,104 L136,160 L64,160 Z", "#2a9d4a") + circle(130, 60, 16, "#e05d8a"))
    snow = "".join(circle(40 + (i * 37) % 120, 30 + (i * 53) % 120, 3, "#ffffff") for i in range(14))
    base = path("M30,150 L170,150 L186,230 L14,230 Z", "#c8302b") + rect(24, 150, 152, 18, "#f2f2ee", r=4) + \
        "".join(circle(30 + i * 24, 196, 7, "#2a9d4a") for i in range(7))
    return svg(200, 232, base, glass, elf, snow, gloss(52, 26, 16, 60, 0.6))


@drawing
def soccercleat01():
    black = "#1b1b1d"
    upper = path("M20,100 Q10,60 60,50 L130,20 Q160,10 180,30 L200,60 Q260,70 300,96 Q316,110 300,120 L30,124 "
                 "Q16,118 20,100 Z", black)
    sole = rect(18, 116, 288, 16, "#2b2b2e", r=6)
    studs = "".join(rect(40 + i * 40, 128, 14, 14, "#4a4a4e", r=3) for i in range(7))
    stripes = "".join(stroke(f"M{120 + i * 20},40 L{150 + i * 22},110", "#f2f2ee", 7) for i in range(3))
    laces = "".join(stroke(f"M{190 + i * 16},{58 + i * 6} L{176 + i * 16},{78 + i * 6}", "#f2f2ee", 4) for i in range(5))
    return svg(320, 144, upper, sole, studs, stripes, laces, gloss(40, 70, 60, 8, 0.2, r=4))


@drawing
def stubbywrench01a():
    steel, dark = "#a9afb7", "#7d838c"
    hexagon = " ".join(f"{50 + 17 * math.cos(math.radians(a))},{44 + 17 * math.sin(math.radians(a))}"
                       for a in range(0, 360, 30))
    ring = path(f"M10,44 A40,40 0 1 0 90,44 A40,40 0 1 0 10,44 Z M{hexagon.replace(' ', ' L', 0)} Z".replace(
        f"M{hexagon}", "M" + " L".join(hexagon.split(" "))), steel, 'fill-rule="evenodd"')
    shaft = rect(80, 30, 176, 28, steel, r=12)
    jaw = path("M246,8 L304,8 Q322,8 322,30 L322,58 Q322,80 304,80 L246,80 Q256,62 284,60 L304,60 L304,28 L284,28 "
               "Q256,26 246,8 Z", steel)
    edge = rect(80, 50, 176, 8, dark, r=4)
    return svg(326, 90, shaft, edge, ring, jaw, gloss(90, 34, 150, 5, 0.6, r=3))


@drawing
def tennisracket():
    frame = ellipse(80, 100, 74, 96, "none", 'stroke="#14141a" stroke-width="12"')
    accent = ellipse(80, 100, 74, 96, "none", 'stroke="#2f62c9" stroke-width="4" stroke-dasharray="60 40"')
    strings = "".join(stroke(f"M{x},14 L{x},186", "#c9cbd0", 1.4) for x in range(20, 142, 10)) + \
        "".join(stroke(f"M10,{y} L150,{y}", "#c9cbd0", 1.4) for y in range(16, 186, 10))
    clip = '<clipPath id="tr"><ellipse cx="80" cy="100" rx="68" ry="90"/></clipPath>'
    throat = path("M54,190 L80,226 L106,190 L96,190 L80,212 L64,190 Z", "#14141a")
    handle = rect(70, 222, 20, 140, "#14141a", r=6) + rect(68, 300, 24, 64, "#2f62c9", r=6)
    return svg(160, 366, clip, f'<g clip-path="url(#tr)">{strings}</g>', frame, accent, throat, handle)


@drawing
def tie02():
    silk = "#d8c3a0"
    knot = path("M40,0 L80,0 L74,40 L46,40 Z", mix(silk, -0.1))
    blade = path("M46,38 L74,38 L96,300 L60,340 L24,300 Z", silk)
    shade = path("M60,38 L74,38 L96,300 L60,340 Z", "#000000", 'opacity="0.08"')
    sheen = path("M50,60 L58,60 L44,290 L36,284 Z", "#ffffff", 'opacity="0.35"')
    return svg(120, 342, blade, shade, sheen, knot)


@drawing
def travelmug():
    steel = "#b8bcc2"
    defs, body = cylinder(10, 50, 140, 210, steel, top=mix(steel, 0.1), cap=0.1)
    lid = rect(4, 18, 152, 46, "#1c1c1e", r=10) + rect(40, 8, 60, 14, "#2a2a2e", r=4)
    handle = path("M150,90 Q196,90 196,150 Q196,206 150,206 L150,186 Q176,186 176,150 Q176,110 150,110 Z", "#1c1c1e")
    base = rect(10, 250, 140, 12, "#1c1c1e", r=4)
    return svg(200, 264, handle, body, lid, base, gloss(26, 80, 12, 160, 0.55), defs=defs)


@drawing
def triangleruler01():
    plate = path("M0,110 L300,110 L60,0 Z M74,96 L206,96 L84,40 Z", "#aeb3b9", 'fill-rule="evenodd" opacity="0.92"')
    edge = poly([(0, 110), (300, 110), (300, 114), (0, 114)], "#81868c")
    marks = "".join(stroke(f"M{10 + i * 14},110 L{10 + i * 14},{104 if i % 5 else 98}", "#4a4d52", 1.4)
                    for i in range(21))
    return svg(300, 114, plate, edge, marks)


@drawing
def vacuumcleaner01():
    dark = "#2b2e33"
    handle = rect(46, 0, 22, 130, dark, r=10) + rect(40, 0, 34, 24, dark, r=10)
    tube = rect(50, 120, 14, 470, "#4a4e55", r=6)
    body = path("M34,330 Q34,300 58,300 Q84,300 84,330 L84,470 Q84,490 60,490 Q34,490 34,470 Z", dark)
    panel = rect(44, 360, 28, 60, "#3a7bd5", r=6) + rect(48, 372, 20, 8, "#9ecbff", r=2)
    bin_ = rect(38, 430, 42, 50, "#5e6670", r=8, extra='opacity="0.9"')
    head = path("M10,620 Q10,598 40,596 L130,596 Q150,596 150,616 L150,630 L10,630 Z", dark) + \
        rect(14, 622, 132, 8, "#1a1a1d", r=3) + rect(52, 586, 22, 16, dark, r=4)
    return svg(156, 632, tube, handle, body, panel, bin_, head)


@drawing
def visor():
    """Black sun visor, three-quarter view: a band with a white sweatband and a curved brim."""
    black, band_c = "#1d1d20", "#2c2d31"
    band_back = path("M40,70 Q150,0 262,64 L262,86 Q150,24 40,92 Z", mix(band_c, -0.2))
    sweat = path("M52,84 Q150,30 252,84 L252,94 Q150,42 52,96 Z", "#efefea")
    band_front = path("M40,92 Q150,150 262,86 L262,108 Q150,172 40,114 Z", band_c)
    brim = path("M30,110 Q150,176 272,104 Q300,120 286,140 Q160,220 20,150 Q4,128 30,110 Z", black)
    brim_hi = path("M50,132 Q150,180 260,128 Q160,196 50,142 Z", "#ffffff", 'opacity="0.08"')
    return svg(300, 190, band_back, sweat, band_front, brim, brim_hi)


@drawing
def watercolorpaintset():
    tray = poly([(20, 0), (280, 0), (300, 100), (0, 100)], "#f7f7f4")
    edge = poly([(0, 100), (300, 100), (300, 114), (0, 114)], "#dcdcd6")
    colours = ["#d62828", "#f77f00", "#fcbf49", "#90be6d", "#2a9d8f", "#277da1", "#6a4c93", "#3a2a1a", "#f94144",
               "#43aa8b", "#577590", "#e76f51", "#ffb3c6", "#8d99ae", "#2b2d42", "#f4a261"]
    pans = "".join(ellipse(44 + c * 30 + r_ * 4, 24 + r_ * 26, 12, 9, colours[(c + r_ * 8) % 16])
                   for r_ in range(3) for c in range(8))
    return svg(300, 116, tray, edge, pans)
