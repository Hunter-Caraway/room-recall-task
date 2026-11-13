"""Small helpers for drawing objects and rooms as flat SVG illustrations.

Style: flat colours, light from the upper left, shading with hard-edged bands
(no outlines, no soft photographic gradients), slightly rounded corners.
Every drawing is a full SVG document; build_drawn.py renders them to PNG.
"""
from __future__ import annotations

import colorsys
import itertools

_ids = itertools.count()


def uid(prefix: str = "g") -> str:
    return f"{prefix}{next(_ids)}"


def mix(colour: str, amount: float) -> str:
    """Lighten (amount > 0) or darken (amount < 0) a #rrggbb colour."""
    r, g, b = (int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = max(0.0, min(1.0, l + amount * (1 - l if amount > 0 else l)))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def svg(width: float, height: float, *parts: str, defs: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}"><defs>{defs}</defs>{"".join(parts)}</svg>')


def band(colour: str, horizontal: bool = True) -> tuple[str, str]:
    """A flat 'cylinder' fill: a light strip on the left, the base colour, a darker right side.
    Returns (gradient id, gradient definition)."""
    gid = uid("band")
    light, dark = mix(colour, 0.35), mix(colour, -0.28)
    x2, y2 = ("1", "0") if horizontal else ("0", "1")
    stops = [(0, light), (0.16, light), (0.16, colour), (0.68, colour), (0.68, dark), (1, dark)]
    defs = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops) + "</linearGradient>")
    return gid, defs


def rect(x, y, w, h, fill, r=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" {extra}/>'


def ellipse(cx, cy, rx, ry, fill, extra=""):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'


def circle(cx, cy, r, fill, extra=""):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {extra}/>'


def path(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def stroke(d, colour, width, extra=""):
    return (f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" {extra}/>')


def poly(points, fill, extra=""):
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}" {extra}/>'


def text(x, y, s, size, fill, weight="bold", anchor="middle"):
    return (f'<text x="{x}" y="{y}" font-family="DejaVu Sans, Arial, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


def cylinder(x, y, w, h, colour, top=None, cap=0.12):
    """An upright cylinder seen from slightly above: body, bottom curve, top ellipse."""
    gid, defs = band(colour)
    ry = w * cap
    body = (path(f"M{x},{y + ry} L{x},{y + h - ry} A{w / 2},{ry} 0 0 0 {x + w},{y + h - ry} "
                 f"L{x + w},{y + ry} Z", f"url(#{gid})"))
    top_fill = top or mix(colour, 0.2)
    lid = ellipse(x + w / 2, y + ry, w / 2, ry, top_fill)
    return defs, body + lid


def gloss(x, y, w, h, opacity=0.35, r=None):
    """A soft white highlight strip."""
    r = w / 2 if r is None else r
    return rect(x, y, w, h, "#ffffff", r=r, extra=f'opacity="{opacity}"')
