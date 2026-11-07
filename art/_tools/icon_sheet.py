"""Contact sheet of processed icons: python icon_sheet.py <raw_root> <out.png>"""
import sys, pathlib
from PIL import Image
root, out = pathlib.Path(sys.argv[1]), sys.argv[2]
files = [f for r in ("kitchen", "living_room", "hallway") for f in sorted((root / r / "icons").glob("*.png"))]
sheet = Image.new("RGB", (10 * 170, ((len(files) + 9) // 10) * 170), (200, 200, 200))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA")
    box = im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    im = im.crop(box)
    k = 150 / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cell = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    cell.paste(im, ((160 - im.width) // 2, (160 - im.height) // 2), im)
    sheet.paste(cell, ((i % 10) * 170 + 5, (i // 10) * 170 + 5), cell)
sheet.save(out)
