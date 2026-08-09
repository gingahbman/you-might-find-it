#!/usr/bin/env python3
"""Walk Microfiche Photos, record every image's size/aspect/mean-brightness/saturation.

Writes inventory.json + prints a per-folder summary.
"""
import os, json, sys
from PIL import Image, ImageStat

SRC = "/Users/sundeepbasi/Workbench/TIME CAPSULE/Microfiche Photos"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp", ".tif", ".tiff"}

rows = []
for root, dirs, names in os.walk(SRC):
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for n in sorted(names):
        ext = os.path.splitext(n)[1].lower()
        if ext not in EXTS:
            continue
        p = os.path.join(root, n)
        rel = os.path.relpath(p, SRC)
        folder = os.path.dirname(rel) or "(root)"
        try:
            im = Image.open(p)
            w, h = im.size
            rgb = im.convert("RGB")
            small = rgb.resize((64, 64))
            st = ImageStat.Stat(small)
            mean = st.mean
            bright = sum(mean) / 3
            sat = max(mean) - min(mean)
            hsv = small.convert("HSV")
            satmean = ImageStat.Stat(hsv).mean[1]
            alpha = "A" in im.getbands() or im.mode == "P" and "transparency" in im.info
        except Exception as e:
            print("ERR", rel, str(e)[:70], file=sys.stderr)
            continue
        rows.append(dict(rel=rel, folder=folder, name=n, w=w, h=h,
                         ar=round(w / h, 3), px=w * h,
                         bytes=os.path.getsize(p),
                         bright=round(bright, 1), sat=round(satmean, 1),
                         alpha=bool(alpha)))

json.dump(rows, open(os.path.join(os.path.dirname(__file__), "inventory.json"), "w"), indent=1)

by = {}
for r in rows:
    by.setdefault(r["folder"], []).append(r)
print(f"{len(rows)} images in {len(by)} folders\n")
print(f"{'folder':38} {'n':>3}  {'min-dim':>9}  {'max-dim':>9}  {'aspect':>12}  {'bright':>6} {'sat':>5}  alpha")
for f in sorted(by):
    rs = by[f]
    dims = [min(r['w'], r['h']) for r in rs]
    ars = [r['ar'] for r in rs]
    print(f"{f[:38]:38} {len(rs):3}  "
          f"{min(dims):9}  {max(dims):9}  "
          f"{min(ars):5.2f}-{max(ars):5.2f}  "
          f"{sum(r['bright'] for r in rs)/len(rs):6.1f} "
          f"{sum(r['sat'] for r in rs)/len(rs):5.1f}  "
          f"{sum(1 for r in rs if r['alpha'])}")
