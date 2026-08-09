#!/usr/bin/env python3
"""Audit the prepared tiles: what got cropped, what got letterboxed, what is just text."""
import os, re, json, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageStat, ImageFilter, ImageDraw, ImageFont
import prepare as P

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/sundeepbasi/Workbench/TIME CAPSULE/Microfiche Photos"
tiles = json.loads(re.search(r"const TILES=(\[.*?\]);",
                             open(os.path.join(HERE, "site/manifest.js")).read(), re.S).group(1))
inv = {r["rel"]: r for r in json.load(open(os.path.join(HERE, "inventory.json")))}

rows = []
for t in tiles:
    src = inv[t["src"]]
    src_ar = src["w"] / src["h"]
    blk_ar = t["bw"] / t["bh"]
    # how much of the source survives the crop to the block aspect
    keep = min(src_ar, blk_ar) / max(src_ar, blk_ar)
    letterboxed = keep < P.LETTERBOX_KEEP
    im = Image.open(os.path.join(HERE, "site/tiles", t["id"] + ".jpg"))
    g = im.convert("L")
    small = g.resize((96, 96))
    edge = ImageStat.Stat(small.filter(ImageFilter.FIND_EDGES)).mean[0]
    hist = small.histogram()
    tot = sum(hist)
    pale = sum(hist[200:]) / tot          # paper-white fraction
    sat = ImageStat.Stat(im.convert("HSV")).mean[1]
    # cheap "is this a wall of small type" test: bright ground + lots of fine edges + no colour
    texty = pale > 0.42 and edge > 8 and sat < 60
    rows.append(dict(t, src_ar=round(src_ar, 2), keep=round(keep, 2),
                     lb=letterboxed, texty=texty, sat=round(sat), edge=round(edge, 1),
                     pale=round(pale, 2), cells=t["bw"] * t["bh"]))

print(f"{len(rows)} works\n")
print("— cropped hardest (fraction of the source that survives) —")
for r in sorted(rows, key=lambda r: r["keep"])[:16]:
    tag = "letterboxed" if r["lb"] else "CROPPED"
    print(f"  keep {r['keep']:4.2f}  {r['bw']}x{r['bh']}  src {r['src_ar']:5.2f}  {tag:11}  {r['p']} · {r['t']}")

big = [r for r in rows if r["cells"] >= 3]
print(f"\n— {len(big)} blocks of 3+ cells —")
for r in sorted(big, key=lambda r: -r["cells"]):
    print(f"  {r['bw']}x{r['bh']}  sat {r['sat']:3}  pale {r['pale']:4.2f}  "
          f"{'TEXT' if r['texty'] else '    '}  {r['p']} · {r['t']}")

texty = [r for r in rows if r["texty"]]
print(f"\n— {len(texty)} works read as walls of type ({sum(r['cells'] for r in texty)} cells) —")
for r in sorted(texty, key=lambda r: -r["cells"]):
    print(f"  {r['bw']}x{r['bh']}  {r['p']} · {r['t']}")

print("\n— colour —")
dull = sorted(rows, key=lambda r: r["sat"])
print(f"  median saturation {sorted(r['sat'] for r in rows)[len(rows)//2]}")
print(f"  {sum(1 for r in rows if r['sat'] < 45)} works under sat 45 "
      f"({sum(r['cells'] for r in rows if r['sat'] < 45)} cells)")
for r in dull[:10]:
    print(f"  sat {r['sat']:3}  {r['bw']}x{r['bh']}  {r['p']} · {r['t']}")

json.dump(rows, open(os.path.join(HERE, "audit.json"), "w"), indent=1)
