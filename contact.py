#!/usr/bin/env python3
"""Contact sheets of every source image, grouped by folder, with index labels."""
import os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("ARCHIVE_SRC",
                     os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  os.pardir, "Microfiche Photos"))
OUT = os.path.join(HERE, "sheets")
os.makedirs(OUT, exist_ok=True)

rows = json.load(open(os.path.join(HERE, "inventory.json")))
by = {}
for r in rows:
    by.setdefault(r["folder"], []).append(r)

CELL, PAD, HDR = 190, 8, 34
COLS = 8
try:
    f_hdr = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
    f_cap = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 11)
except OSError:
    f_hdr = f_cap = ImageFont.load_default()

# pack folders into sheets of <= 40 cells
sheets, cur, curn = [], [], 0
for f in sorted(by):
    n = len(by[f])
    if curn and curn + n > 48:
        sheets.append(cur); cur, curn = [], 0
    cur.append(f); curn += n
if cur:
    sheets.append(cur)

gi = 0
for si, folders in enumerate(sheets, 1):
    blocks = []
    for f in folders:
        rs = by[f]
        nrow = math.ceil(len(rs) / COLS)
        blocks.append((f, rs, nrow))
    H = sum(HDR + b[2] * (CELL + 18 + PAD) + 14 for b in blocks) + PAD
    W = COLS * (CELL + PAD) + PAD
    sheet = Image.new("RGB", (W, H), (24, 25, 29))
    d = ImageDraw.Draw(sheet)
    y = PAD
    for f, rs, nrow in blocks:
        d.text((PAD, y + 6), f"{f}   ({len(rs)})", font=f_hdr, fill=(240, 236, 228))
        y += HDR
        for i, r in enumerate(rs):
            cx = PAD + (i % COLS) * (CELL + PAD)
            cy = y + (i // COLS) * (CELL + 18 + PAD)
            p = os.path.join(SRC, r["rel"])
            try:
                im = Image.open(p)
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    bg = Image.new("RGBA", im.size, (24, 25, 29, 255))
                    im = Image.alpha_composite(bg, im)
                im = im.convert("RGB")
                im = ImageOps.contain(im, (CELL, CELL), Image.LANCZOS)
            except Exception:
                im = Image.new("RGB", (CELL, CELL), (60, 30, 30))
            sheet.paste(im, (cx + (CELL - im.width) // 2, cy + (CELL - im.height) // 2))
            d.rectangle([cx, cy, cx + CELL, cy + CELL], outline=(60, 62, 70))
            cap = f"[{gi}] {r['name']}"
            d.text((cx + 2, cy + CELL + 3), cap[:34], font=f_cap, fill=(150, 148, 140))
            d.text((cx + 4, cy + 3), f"{gi}", font=f_hdr, fill=(255, 210, 90))
            gi += 1
        y += nrow * (CELL + 18 + PAD) + 14
    sheet.save(os.path.join(OUT, f"sheet_{si:02d}.png"))
    print("sheet", si, folders, sheet.size)
