"""Put object cutouts into a room picture, and draw grid tiles. Pillow only.

The same code adds the unscored filler when the rooms are built (art/) and the
target photos when a session runs, so every object in a room gets the same
treatment and none stands out: scaled to its real size at its spot, turned only
as listed, tinted by the light at the spot, softened to the render's sharpness,
with a contact shadow (or a drop shadow on a wall).
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .stimuli import Item, Spot

SOFTEN_PX = 0.6  # matches the slight softness of the denoised room render
CONTACT_ALPHA = 150
WALL_ALPHA = 95


def _cutout(item: Item) -> Image.Image:
    with Image.open(item.path) as image:
        return image.convert("RGBA")


def prepared(item: Item, spot: Spot) -> Image.Image:
    """The object as it will look at this spot: turned, scaled, lit and softened."""
    image = _cutout(item)
    scale = item.width_m * spot.px_per_m / image.width
    if item.rotate_deg:
        image = image.rotate(item.rotate_deg, resample=Image.BICUBIC, expand=True)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.LANCZOS)
    box = image.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if box:
        image = image.crop(box)
    r, g, b, a = image.split()
    lit = [band.point(lambda v, m=m: min(255, round(v * m))) for band, m in zip((r, g, b), spot.light)]
    image = Image.merge("RGBA", (*lit, a))
    return image.filter(ImageFilter.GaussianBlur(SOFTEN_PX))


def anchor(image: Image.Image, spot: Spot) -> tuple[int, int]:
    """Top-left corner: bottom centre on the spot, or centred on it for a wall."""
    if spot.surface == "wall":
        return round(spot.x - image.width / 2), round(spot.y - image.height / 2)
    return round(spot.x - image.width / 2), round(spot.y - image.height)


def _shadow(size: tuple[int, int], image: Image.Image, spot: Spot, at: tuple[int, int],
            turned: bool = False) -> Image.Image:
    """A greyscale mask of where the shadow darkens the room."""
    mask = Image.new("L", size, 0)
    w, h = image.size
    if turned and spot.surface != "wall":
        # A turned object lies across its box, so an ellipse would miss it: use its own
        # outline, nudged down a little, as if lit from above.
        silhouette = image.getchannel("A").point(lambda v: CONTACT_ALPHA if v > 24 else 0)
        mask.paste(silhouette, (at[0], round(at[1] + max(2.0, 0.04 * h))))
        return mask.filter(ImageFilter.GaussianBlur(max(2.0, 0.025 * max(w, h))))
    if spot.surface == "wall":
        offset = (round(at[0] + 0.02 * w), round(at[1] + 0.03 * h))
        silhouette = image.getchannel("A").point(lambda v: WALL_ALPHA if v > 24 else 0)
        mask.paste(silhouette, offset)
        return mask.filter(ImageFilter.GaussianBlur(max(2.0, 0.03 * max(w, h))))
    width = 0.92 * w
    height = max(3.0, width * spot.squash)
    draw = ImageDraw.Draw(mask)
    cx, cy = spot.x, spot.y - height * 0.3
    draw.ellipse((cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2), fill=CONTACT_ALPHA)
    if spot.surface == "lean":  # also a soft shadow on the wall behind
        silhouette = image.getchannel("A").point(lambda v: WALL_ALPHA // 2 if v > 24 else 0)
        layer = Image.new("L", size, 0)
        layer.paste(silhouette, (round(at[0] + 0.04 * w), round(at[1] - 0.02 * h)))
        mask = ImageChops.lighter(mask, layer)
    return mask.filter(ImageFilter.GaussianBlur(max(2.0, 0.05 * w)))


def compose(room: Image.Image, placements: list[tuple[Item, Spot]]) -> Image.Image:
    """The room with every object placed. Wall objects go on first, then the rest
    from the back of the room (higher on screen) to the front."""
    picture = room.convert("RGB").copy()
    black = Image.new("RGB", picture.size, (0, 0, 0))
    order = sorted(placements, key=lambda p: (p[1].surface != "wall", p[1].y))
    for item, spot in order:
        image = prepared(item, spot)
        at = anchor(image, spot)
        picture = Image.composite(black, picture, _shadow(picture.size, image, spot, at, bool(item.rotate_deg)))
        picture.paste(image, at, image)
    return picture


def tile(item: Item, size: int, fill: float = 0.84) -> Image.Image:
    """A grid tile: the object as photographed (no turn), centred on white."""
    image = _cutout(item)
    image.thumbnail((round(size * fill), round(size * fill)), Image.LANCZOS)
    out = Image.new("RGB", (size, size), (255, 255, 255))
    out.paste(image, ((size - image.width) // 2, (size - image.height) // 2), image)
    return out
