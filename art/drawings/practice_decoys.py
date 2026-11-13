"""Flat drawings of the practice grid's decoys. Not used in scored trials.
DECOYS maps name -> (label, category, real longest side in metres)."""
from __future__ import annotations

from .kit import band, circle, cylinder, ellipse, gloss, mix, path, poly, rect, stroke, svg

DRAW = {}
DECOYS = {}


def decoy(label, category, size_m):
    def register(fn):
        DRAW[fn.__name__] = fn
        DECOYS[fn.__name__] = (label, category, size_m)
        return fn
    return register


@decoy("watering can", "garden", 0.4)
def watering_can():
    green = "#3a8f6a"
    gid, defs = band(green)
    body = path("M60,80 L200,80 L210,230 Q210,240 200,240 L60,240 Q50,240 50,230 Z", f"url(#{gid})")
    spout = path("M200,190 L290,60 L304,70 L214,214 Z", green) + rect(282, 46, 30, 24, mix(green, -0.2), r=4,
                                                                    extra='transform="rotate(35 297 58)"')
    handle = stroke("M70,90 Q70,20 130,20 Q190,20 190,90", mix(green, -0.2), 14)
    return svg(320, 244, handle, spout, body, defs=defs)


@decoy("birdhouse", "decor", 0.3)
def birdhouse():
    wood = "#c79c63"
    roof = poly([(0, 110), (120, 10), (240, 110), (220, 120), (120, 36), (20, 120)], "#b5322b")
    house = poly([(30, 110), (120, 36), (210, 110), (210, 290), (30, 290)], wood)
    hole = circle(120, 160, 26, "#3a2a1a")
    perch = rect(114, 200, 12, 40, "#7b4a26", r=4)
    return svg(240, 294, house, roof, hole, perch)


@decoy("lantern", "decor", 0.3)
def lantern():
    black = "#2a2a2e"
    glass = rect(50, 80, 120, 150, "#f6e6a6") + ellipse(110, 160, 26, 40, "#f6c026")
    frame = (rect(40, 70, 140, 16, black, r=4) + rect(40, 226, 140, 20, black, r=4)
             + rect(44, 80, 10, 150, black) + rect(166, 80, 10, 150, black) + rect(105, 80, 10, 150, black))
    top = poly([(50, 70), (110, 30), (170, 70)], black)
    ring = circle(110, 18, 16, "none", f'stroke="{black}" stroke-width="6"')
    return svg(220, 250, glass, frame, top, ring)


@decoy("spinning top", "toy", 0.08)
def spinning_top():
    body = path("M20,90 Q110,40 200,90 Q170,180 110,230 Q50,180 20,90 Z", "#e63946")
    stripe = path("M30,110 Q110,80 190,110 Q184,126 176,140 Q110,112 44,140 Q36,126 30,110 Z", "#f6c026")
    handle = rect(100, 10, 20, 70, "#5b3a1a", r=6)
    return svg(220, 236, handle, body, stripe, rect(106, 226, 8, 10, "#2a2a2e"))


@decoy("hourglass", "decor", 0.2)
def hourglass():
    wood = "#7b4a26"
    glass = path("M40,30 L160,30 Q160,110 108,140 Q160,170 160,250 L40,250 Q40,170 92,140 Q40,110 40,30 Z",
                 "#e2eef2")
    sand = path("M60,90 L140,90 Q130,120 100,136 Q70,120 60,90 Z", "#e0b862") + \
        path("M100,170 Q150,200 156,246 L44,246 Q50,200 100,170 Z", "#e0b862")
    frame = rect(10, 10, 180, 24, wood, r=6) + rect(10, 246, 180, 24, wood, r=6) + rect(20, 30, 10, 216, wood) + \
        rect(170, 30, 10, 216, wood)
    return svg(200, 274, glass, sand, frame)


@decoy("pepper mill", "kitchen tool", 0.22)
def pepper_mill():
    wood = "#5b3a1a"
    gid, defs = band(wood)
    body = path("M40,60 Q30,120 50,150 Q30,200 30,250 L130,250 Q130,200 110,150 Q130,120 120,60 Z", f"url(#{gid})")
    cap = ellipse(80, 50, 48, 20, mix(wood, 0.1)) + circle(80, 22, 14, "#c4c8cd")
    return svg(160, 254, body, cap, defs=defs)


@decoy("hand bell", "instrument", 0.15)
def hand_bell():
    brass = "#d4a62a"
    gid, defs = band(brass)
    bell = path("M60,90 Q60,40 110,40 Q160,40 160,90 L170,190 Q200,200 200,214 L20,214 Q20,200 50,190 Z",
                f"url(#{gid})")
    handle = rect(96, 0, 28, 50, "#3a2a1a", r=10)
    return svg(220, 230, handle, bell, circle(110, 220, 10, mix(brass, -0.3)), defs=defs)


@decoy("anchor", "decor", 0.4)
def anchor():
    navy = "#264653"
    shank = rect(100, 40, 20, 220, navy)
    ring = circle(110, 30, 22, "none", f'stroke="{navy}" stroke-width="10"')
    stock = rect(50, 70, 120, 16, navy, r=6)
    arms = stroke("M20,190 Q30,270 110,272 Q190,270 200,190", navy, 18) + \
        poly([(4, 200), (20, 170), (36, 200)], navy) + poly([(184, 200), (200, 170), (216, 200)], navy)
    return svg(220, 290, ring, shank, stock, arms)
