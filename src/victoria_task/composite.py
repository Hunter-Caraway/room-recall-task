"""Put object drawings into a room drawing, and draw grid tiles. Pillow only.

The same code adds the unscored filler when the rooms are built (art/build_drawn.py)
and the targets when a session runs, so every object in a room gets the same
treatment and none stands out: scaled to its real size at its spot, with a flat
shadow in the illustration's style (an ellipse under a standing object, a copy of
the outline on the wall behind a hanging or leaning one).
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from .stimuli import Item, Spot

SHADOW = (0, 0, 0, 56)  # flat shadow colour, as drawn in the rooms
WALL_SHADOW_OFFSET = (0.035, 0.025)  # of the object's size: right and down, light from the upper left


def _drawing(item: Item) -> Image.Image:
    with Image.open(item.path) as image:
        return image.convert("RGBA")


def prepared(item: Item, spot: Spot) -> Image.Image:
    """The drawing scaled to its real size at this spot."""
    w_m, h_m = spot.size(item)
    size = (max(1, round(w_m * spot.px_per_m)), max(1, round(h_m * spot.px_per_m)))
    return _drawing(item).resize(size, Image.LANCZOS)


def anchor(image: Image.Image, spot: Spot) -> tuple[int, int]:
    """Top-left corner: hanging from the hook on a wall, otherwise standing on the spot."""
    if spot.surface == "wall":
        return round(spot.x - image.width / 2), round(spot.y)
    return round(spot.x - image.width / 2), round(spot.y - image.height)


def _outline_shadow(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A").point(lambda v: SHADOW[3] if v > 128 else 0)
    shadow = Image.new("RGBA", image.size, SHADOW[:3] + (0,))
    shadow.putalpha(alpha)
    return shadow


def _base_width(image: Image.Image) -> tuple[int, int]:
    """Left and right edge of the drawing within its lowest tenth."""
    rows = max(1, image.height // 10)
    band = image.getchannel("A").crop((0, image.height - rows, image.width, image.height))
    box = band.point(lambda v: 255 if v > 128 else 0).getbbox()
    return (box[0], box[2]) if box else (0, image.width)


def compose(room: Image.Image, placements: list[tuple[Item, Spot]]) -> Image.Image:
    """The room with every object placed. Wall objects go on first, then the rest
    from the back of the room (higher on screen) to the front."""
    picture = room.convert("RGBA").copy()
    order = sorted(placements, key=lambda p: (p[1].surface != "wall", p[1].y))
    for item, spot in order:
        image = prepared(item, spot)
        x, y = anchor(image, spot)
        shade = Image.new("RGBA", picture.size, (0, 0, 0, 0))
        if spot.surface in ("wall", "lean"):
            dx, dy = round(WALL_SHADOW_OFFSET[0] * image.width) + 3, round(WALL_SHADOW_OFFSET[1] * image.height) + 2
            shade.paste(_outline_shadow(image), (x + dx, y + dy))
        if spot.surface != "wall":
            lo, hi = _base_width(image)
            width = max(8, (hi - lo) * 1.15)
            depth = max(4, width * 0.16)
            cx = x + (lo + hi) / 2 + width * 0.06
            ImageDraw.Draw(shade).ellipse((cx - width / 2, spot.y - depth * 0.6, cx + width / 2, spot.y + depth * 0.4),
                                          fill=SHADOW)
        picture = Image.alpha_composite(picture, shade)
        picture.alpha_composite(image, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    return picture.convert("RGB")


def tile(item: Item, size: int, fill: float = 0.84) -> Image.Image:
    """A grid tile: the object's drawing, centred on white."""
    image = _drawing(item)
    image.thumbnail((round(size * fill), round(size * fill)), Image.LANCZOS)
    out = Image.new("RGB", (size, size), (255, 255, 255))
    out.paste(image, ((size - image.width) // 2, (size - image.height) // 2), image)
    return out
