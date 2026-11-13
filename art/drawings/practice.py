"""Flat drawings of the four practice targets (made objects; the practice grid shows
their studio shots)."""
from __future__ import annotations

from .kit import band, circle, cylinder, ellipse, gloss, mix, path, rect, stroke, svg

DRAW = {}


def drawing(fn):
    DRAW[fn.__name__] = fn
    return fn


@drawing
def ceramic_vase_04():
    white = "#ecebe7"
    body = path("M60,40 L100,40 L100,70 Q160,120 156,220 Q152,290 80,290 Q8,290 4,220 Q0,120 60,70 Z", white)
    shade = path("M100,70 Q160,120 156,220 Q152,290 80,290 Q130,270 132,200 Q134,120 100,70 Z", "#000000",
                 'opacity="0.08"')
    lip = ellipse(80, 40, 22, 6, mix(white, -0.15))
    handle = stroke("M100,52 C140,40 140,90 108,96", mix(white, -0.06), 9)
    return svg(160, 292, handle, body, shade, lip, gloss(30, 120, 10, 100, 0.5))


@drawing
def brass_vase_03():
    copper = "#c8835a"
    gid, defs = band(copper)
    body = path("M30,10 L90,10 L78,40 Q110,80 106,150 Q102,200 76,220 L80,250 L98,262 L98,272 L22,272 L22,262 "
                "L40,250 L44,220 Q18,200 14,150 Q10,80 42,40 Z", f"url(#{gid})")
    lip = ellipse(60, 10, 30, 7, mix(copper, -0.2))
    bands = rect(26, 100, 68, 8, mix(copper, -0.25)) + rect(22, 170, 76, 8, mix(copper, -0.25))
    return svg(120, 274, body, lip, bands, defs=defs)


@drawing
def ceramic_pot():
    clay = "#a0896a"
    defs, body = cylinder(30, 50, 200, 150, clay, top=mix(clay, -0.1), cap=0.14)
    lid = ellipse(130, 58, 104, 26, mix(clay, 0.08)) + ellipse(130, 40, 26, 12, mix(clay, -0.15))
    handles = path("M30,100 Q0,100 4,124 Q8,138 30,132 Z", mix(clay, -0.1)) + \
        path("M230,100 Q260,100 256,124 Q252,138 230,132 Z", mix(clay, -0.1))
    return svg(260, 204, handles, body, lid, defs=defs)


@drawing
def pocket_watch():
    gold = "#c9b27a"
    return svg(200, 260, circle(100, 32, 24, "none", f'stroke="{gold}" stroke-width="8"'),
               rect(90, 50, 20, 22, gold, r=4), circle(100, 160, 96, gold), circle(100, 160, 84, "#f7f5ee"),
               "".join(rect(98, 82, 4, 12, "#55524a", extra=f'transform="rotate({a} 100 160)"') for a in range(0, 360, 30)),
               stroke("M100,160 L100,100", "#2a2a2a", 4), stroke("M100,160 L140,180", "#2a2a2a", 3),
               gloss(46, 100, 14, 50, 0.4))
