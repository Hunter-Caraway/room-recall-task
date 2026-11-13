"""Cut each object photo out of its white background.

The dataset photos sit on pure white (255, 255, 255). A pixel is background when it
is near-white and connected to the image border, or when it is part of an enclosed
pure-white hole (the gaps inside a key ring or between racket strings). Object
whites are rarely exactly 255 over a large area, so they stay.

Usage: python art/cutout_photos.py SOURCE_DIR OUT_DIR [--sheet SHEET.jpg]
Writes OUT_DIR/<name>.png (RGBA, cropped to the object) and prints one line per photo.
"""
import argparse
import pathlib

import numpy as np
from PIL import Image
from scipy import ndimage

NEAR_WHITE = 247  # every channel at least this: background candidate
PURE_WHITE = 254  # enclosed holes must be this white to count as background
MIN_HOLE = 400  # px; smaller enclosed white patches are highlights, not holes
# Photos whose pure-white enclosed areas are part of the object (a white sticker).
KEEP_WHITE_HOLES = {"rubikcube"}


def cut(path):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    low = rgb.min(axis=2)
    candidate = low >= NEAR_WHITE
    labels, _ = ndimage.label(candidate)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, border[border > 0])
    holes, count = ndimage.label((low >= PURE_WHITE) & ~background)
    if count and pathlib.Path(path).stem not in KEEP_WHITE_HOLES:
        sizes = ndimage.sum(np.ones_like(low), holes, index=np.arange(1, count + 1))
        big = np.flatnonzero(sizes >= MIN_HOLE) + 1
        background |= np.isin(holes, big)
    solid = ndimage.binary_opening(~background, iterations=1)
    keep, count = ndimage.label(solid)
    if count > 1:  # drop specks left by JPEG noise
        sizes = ndimage.sum(solid, keep, index=np.arange(1, count + 1))
        solid = np.isin(keep, np.flatnonzero(sizes >= 0.002 * sizes.max()) + 1)
    # Soft 1-2 px edge, then remove the white fringe the edge pixels carry.
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(solid).astype(np.float32), 0.8)
    alpha = np.clip(alpha, 0, 1)
    safe = np.maximum(alpha, 1e-3)[..., None]
    colour = np.clip((rgb - (1 - safe) * 255.0) / safe, 0, 255)
    rgba = np.dstack([colour, alpha * 255]).astype(np.uint8)
    image = Image.fromarray(rgba, "RGBA")
    box = image.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return image.crop(box), box


def sheet(images, target, tile=220, columns=7):
    rows = (len(images) + columns - 1) // columns
    # A dark background shows any white fringe or missing hole.
    out = Image.new("RGB", (columns * tile, rows * tile), (70, 72, 76))
    for i, (_, image) in enumerate(images):
        thumb = image.copy()
        thumb.thumbnail((tile - 20, tile - 20))
        x, y = (i % columns) * tile, (i // columns) * tile
        out.paste(thumb, (x + (tile - thumb.width) // 2, y + (tile - thumb.height) // 2), thumb)
    out.save(target, quality=88)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("out")
    parser.add_argument("--sheet")
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    for path in sorted(pathlib.Path(args.source).glob("*.jpg")):
        image, box = cut(path)
        image.save(out / f"{path.stem}.png", optimize=True)
        done.append((path.stem, image))
        print(f"{path.stem:24s} {image.width}x{image.height}")
    if args.sheet:
        sheet(done, args.sheet)


if __name__ == "__main__":
    main()
