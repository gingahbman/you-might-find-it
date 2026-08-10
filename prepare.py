#!/usr/bin/env python3
"""Turn the archive into mosaic tiles.

Images: flatten transparency, trim flat borders symmetrically, give each work a block the
shape of its own proportions, crop toward the detail (or letterbox rather than crop hard),
then write a full-colour tile and an exposure-corrected grey thumbnail.

Writing: the passages in writing.py are *set as type* here and written out as tiles of the
same kind. A screenshot of prose is grey noise at mosaic scale; type set at the tile's own
size is legible at the same zoom that makes an image legible.

Outputs site/tiles/*.jpg, site/thumbs/*.jpg and site/manifest.js
"""
import os, re, json, sys, math
from PIL import (Image, ImageChops, ImageFilter, ImageOps, ImageStat, ImageEnhance,
                 ImageDraw, ImageFont)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from projects import PROJECTS, HEROES, RENAME, EXCLUDE, LINKS, TITLES
from writing import PASSAGES

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/sundeepbasi/Workbench/TIME CAPSULE/Microfiche Photos"
SITE = os.path.join(HERE, "site")
# Rendered pixels per grid cell. This is the resolution ceiling of the whole piece: the
# page refuses to zoom past what it buys (see maxS in index.html), so raising it buys
# deeper zoom at the cost of disk.
CELL_PX, THUMB_CELL = 600, 100
MAX_CELLS = 4                       # longest a single work may run
# How much of a work must survive the crop to its block. Below this it is letterboxed
# instead. Set generously: cropping an app icon to fit a rectangle beheads the artwork.
LETTERBOX_KEEP = 0.82
# How many grid cells the archive should add up to. This is the knob that decides the X:
# see grow_to_target(). ~640 lands on the middle stroke weights that read best.
TARGET_CELLS = 640
COLOUR_LIFT, CONTRAST_LIFT = 1.14, 1.05   # applied to the full tiles, never the plate
# At-rest exposure band. The floor is the important number: the page ground is ~#0b0c10,
# so anything that lands below ~60 reads as a hole in the silhouette rather than a tile.
THUMB_MEAN, THUMB_FLOOR, THUMB_CEIL = 150, 74, 236
GROUND = (14, 15, 18)
TRIM_TOL = 14          # how different from the border colour counts as content

for d in ("tiles",):
    os.makedirs(os.path.join(SITE, d), exist_ok=True)


def flatten(im):
    """RGB image on the archive ground, transparency removed."""
    if im.mode == "P" and "transparency" in im.info:
        im = im.convert("RGBA")
    if im.mode in ("RGBA", "LA"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, GROUND + (255,))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def border_colour(im):
    """Most common of the four corner pixels."""
    w, h = im.size
    px = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    return max(set(px), key=px.count)


def autotrim(im):
    """Crop away a flat, uniform frame — symmetrically, and never far.

    The obvious version (crop to the content's bounding box) beheads artwork. On a ground
    that is a gradient rather than a flat colour the mask comes out lopsided, so the crop
    is lopsided too: it took the Feelabit rabbit's ears off and cut the heart in half. So
    trim the *same* amount from opposite sides, keep a square source square, and refuse to
    take more than a third of any side — an icon's margin is part of its design.
    """
    w, h = im.size
    bg = border_colour(im)
    diff = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L")
    box = diff.point(lambda v: 255 if v > TRIM_TOL else 0).getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    pad = int(min(w, h) * 0.03)
    mx, my = max(0, min(x0, w - x1) - pad), max(0, min(y0, h - y1) - pad)
    if abs(w / h - 1) < 0.03:                     # square source stays square
        mx = my = min(mx, my)
    mx, my = min(mx, int(w * 0.34)), min(my, int(h * 0.34))
    return im.crop((mx, my, w - mx, h - my)) if (mx or my) else im


def energy_profile(im, horizontal=True):
    """Mean edge energy per column (or row), as a list."""
    w, h = im.size
    n = 96
    if horizontal:
        small = im.convert("L").resize((n, 24), Image.BILINEAR)
    else:
        small = im.convert("L").resize((24, n), Image.BILINEAR)
    e = small.filter(ImageFilter.FIND_EDGES)
    line = e.resize((n, 1), Image.BOX) if horizontal else e.resize((1, n), Image.BOX)
    return list(line.getdata()), n



def is_type(im):
    """True for a work that is really a wall of small type: a page grab, a slide, a
    marketing screenshot. These are unreadable at any size the mosaic can give them, so
    they get one cell and act as texture rather than eating four cells of the X."""
    g = im.convert("L").resize((96, 96), Image.BILINEAR)
    edge = ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).mean[0]
    hist = g.histogram()
    pale = sum(hist[200:]) / sum(hist)
    sat = ImageStat.Stat(im.convert("HSV")).mean[1]
    return pale > 0.40 and edge > 7 and sat < 62


def block_for(im, hero):
    """How many grid cells this work should occupy, as (across, down).

    A 12:1 banner or a phone screenshot has no square in it worth cropping to, so instead
    of slicing the work into fragments it gets a block the right shape and stays whole.
    """
    w, h = im.size
    ar = w / h
    if ar >= 1.75:
        bw, bh = min(MAX_CELLS, max(2, round(ar))), 1
    elif ar <= 0.58:
        bw, bh = 1, min(MAX_CELLS, max(2, round(1 / ar)))
    else:
        bw = bh = 1
    if hero:                                   # heroes read at twice the size
        bw, bh = min(MAX_CELLS, bw * 2), min(MAX_CELLS, bh * 2)
    return bw, bh


def fit_block(im, bw, bh):
    """Bring the image to the block's aspect, keeping the busiest part of the frame.

    Blocks stop at four cells, so a 12:1 banner still doesn't fit one. Rather than crop
    two thirds of it away, anything this far off gets letterboxed onto the ground colour
    and shown whole — smaller, but readable.
    """
    want = bw / bh
    w, h = im.size
    have = w / h
    if abs(have - want) < 0.02:
        return im
    if min(have, want) / max(have, want) < LETTERBOX_KEEP:
        return ImageOps.pad(im, (bw * CELL_PX, bh * CELL_PX),
                            method=Image.LANCZOS, color=GROUND, centering=(0.5, 0.5))
    if have > want:                            # too wide: slide a window horizontally
        s = int(round(h * want))
        prof, n = energy_profile(im, True)
        win = max(1, int(round(n * s / w)))
    else:                                      # too tall: slide it vertically
        s = int(round(w / want))
        prof, n = energy_profile(im, False)
        win = max(1, int(round(n * s / h)))
    ps = [0]
    for v in prof:
        ps.append(ps[-1] + v)
    best, bi = -1, 0
    for i in range(0, max(1, n - win + 1)):
        v = ps[min(i + win, n)] - ps[i]
        if v > best:
            best, bi = v, i
    if have > want:
        x = max(0, min(w - s, int(round(bi / n * w))))
        return im.crop((x, 0, x + s, h))
    y = max(0, min(h - s, int(round(bi / n * h))))
    return im.crop((0, y, w, y + s))


# ---------------------------------------------------------------- the writing, as type
FONT_DIR = "/Users/sundeepbasi/Workbench/TIME CAPSULE/START/fonts"
PAPER, INK, MUTED, RULE = (235, 228, 214), (25, 26, 31), (129, 123, 108), (196, 187, 169)


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def _wrap(draw, text, font, width):
    """Word-wrap, keeping any line breaks the author put there (the poems need them)."""
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if draw.textlength(trial, font=font) <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _fit(draw, text, name, width, height, hi, lo=13, leading=1.42):
    """Largest size at which the passage still fits the box."""
    while hi > lo:
        f = _font(name, hi)
        lines = _wrap(draw, text, f, width)
        if len(lines) * hi * leading <= height:
            return f, lines
        hi -= 1
    f = _font(name, lo)
    return f, _wrap(draw, text, f, width)


def passage_block(words):
    """A short line wants to be wide and large; a paragraph wants a square."""
    return (2, 1) if words <= 17 else (2, 2)


def render_passage(work, bw, bh):
    """Set the passage as type on a page. This is the whole point: a screenshot of prose
    is grey noise at mosaic scale, but type set at the tile's own size is readable at the
    same zoom that makes an image readable."""
    W_, H_ = bw * CELL_PX, bh * CELL_PX
    im = Image.new("RGB", (W_, H_), PAPER)
    d = ImageDraw.Draw(im)
    m = int(min(W_, H_) * 0.10)
    inner = W_ - 2 * m
    y = m

    tf, tlines = _fit(d, work["title"], "DMSerifDisplay.ttf", inner,
                      H_ * 0.34, int(H_ * (0.20 if bh == 1 else 0.115)), 20, 1.16)
    for ln in tlines:
        d.text((m, y), ln, font=tf, fill=INK)
        y += int(tf.size * 1.16)

    y += int(m * 0.42)
    d.line([(m, y), (m + inner * 0.34, y)], fill=RULE, width=2)
    y += int(m * 0.52)

    foot = int(m * 0.95) if work.get("attrib") else 0
    avail = H_ - y - m - foot
    # size the body to the room it actually has, not to the tile — otherwise a four-line
    # poem on a wide block gets set at caption size and floats in a sea of paper
    bf, blines = _fit(d, work["body"], "Sora.ttf", inner, avail, int(avail / 2.0))
    y += max(0, (avail - int(len(blines) * bf.size * 1.42)) // 2)   # sit it in its space
    for ln in blines:
        d.text((m, y), ln, font=bf, fill=INK)
        y += int(bf.size * 1.42)

    if work.get("attrib"):
        af = _font("Sora.ttf", max(12, int(H_ * 0.022)))
        d.text((m, H_ - m - af.size), " ".join(work["attrib"].upper()[:64]),
               font=af, fill=MUTED)
    return im


def microfiche(im):
    """The at-rest thumbnail: grey, evenly exposed, so the X reads as one solid form.

    Left alone, a near-black screenshot and a white product shot sit side by side and
    the silhouette falls apart. Pulling every tile to the same mean luminance turns the
    mosaic into a single silver plate — the colour only comes back on the full tiles.
    """
    g = ImageOps.autocontrast(im.convert("L"), cutoff=2)
    # A dark app screenshot with one bright logo has a perfectly respectable *mean* and
    # still reads as a black hole, because almost every pixel in it is black. Spread the
    # histogram first, then put the *median* on the target — that is what actually moves
    # the bulk of the tile onto the plate.
    g = Image.blend(g, ImageOps.equalize(g), 0.6)
    hist, tot, c = g.histogram(), g.width * g.height, 0
    med = 128
    for v, n in enumerate(hist):
        c += n
        if c >= tot / 2:
            med = v
            break
    med = max(3, min(252, med))
    gamma = max(0.40, min(2.2, math.log(THUMB_MEAN / 255) / math.log(med / 255)))
    g = g.point([min(255, int(255 * (v / 255) ** gamma)) for v in range(256)])
    g = ImageEnhance.Contrast(g).enhance(0.86)   # keep detail, lose the extremes
    return g.point(lambda v: int(THUMB_FLOOR + v * (THUMB_CEIL - THUMB_FLOOR) / 255))


def pretty(name):
    t = os.path.splitext(name)[0]
    for a, b in RENAME:
        if t.startswith(a):
            t = b + t[len(a):]
    t = re.sub(r"^\d{1,2}[-_ ]", "", t)                    # 01-foo -> foo
    t = re.sub(r"[-_]+", " ", t).strip()
    t = re.sub(r"\s*\b(4x|2x|source|raw|png|jpg)\b\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t)
    if t.islower() or t.isupper():
        t = t.title()
    return t[:52] or "Untitled"


def analyse(inv):
    """Decide every work's block, without writing anything yet."""
    specs = []
    for r in sorted(inv, key=lambda r: (r["folder"], r["name"])):
        if r["rel"] in EXCLUDE:
            continue
        proj, cat, kind = PROJECTS.get(r["folder"], (r["folder"], "Other", "image"))
        hero = r["rel"] in HEROES
        try:
            im = autotrim(flatten(Image.open(os.path.join(SRC, r["rel"]))))
        except Exception as e:
            print("skip", r["rel"], str(e)[:60])
            continue
        typey = is_type(im)
        if typey:
            # Small, but still its own shape — forcing a 3:1 phone screenshot into a
            # square just letterboxes it down to a sliver in a black cell.
            hero = False
            ar = im.width / im.height
            bw, bh = (2, 1) if ar >= 1.4 else (1, 2) if ar <= 0.72 else (1, 1)
        else:
            bw, bh = block_for(im, hero)
        specs.append(dict(rel=r["rel"], p=proj, c=cat, k=kind,
                          t=TITLES.get(r["rel"]) or pretty(r["name"]),
                          hero=hero, typey=typey, bw=bw, bh=bh,
                          px=r["px"], sat=r["sat"]))
    for w in PASSAGES:
        bw, bh = passage_block(len(w["body"].split()))
        specs.append(dict(rel=w["src"], p=w["project"], c="Writing", k="text", t=w["title"],
                          hero=False, typey=False, bw=bw, bh=bh, px=0, sat=0, passage=w))
    return specs


def grow_to_target(specs):
    """Give more works a 2×2 until the archive asks for about TARGET_CELLS cells.

    The X is built on whole cells, so its proportions are decided by how many cells the
    works add up to. Left alone the archive wanted ~490, which only tiles cleanly as a very
    thin X or a very fat one; the handsome middle weights need ~640. Rather than have the
    page paper over the gap by scaling tiles up at run time, the extra cells are decided
    here, where a promoted work is *rendered* at 2×2 and is genuinely sharper for it.
    """
    demand = sum(s["bw"] * s["bh"] for s in specs)
    cands = [s for s in specs if s["bw"] == 1 and s["bh"] == 1 and not s["typey"]]
    cands.sort(key=lambda s: -(s["px"] * (s["sat"] + 40)))    # big and colourful first
    grown = 0
    for s in cands:
        if demand + 3 > TARGET_CELLS:
            break
        s["bw"] = s["bh"] = 2
        demand += 3
        grown += 1
    return demand, grown


def pack_plate(thumbs):
    """All 284 grey thumbnails packed into one image.

    The plate is always shown in full — every thumbnail loads on every visit — so there is
    nothing to gain from keeping them as separate files, and ~285 requests to lose. One
    spritesheet makes the whole X pop in at once, and it turns deployment from "upload 284
    files" into "upload one". Each sprite carries a 2px replicated-edge gutter so fractional
    background-position sampling can never bleed a neighbour in.
    """
    PAD, MAXW = 2, 2560
    order = sorted(range(len(thumbs)), key=lambda i: -thumbs[i].height)
    pos = [None] * len(thumbs)
    x = y = shelf = 0
    for i in order:
        w, h = thumbs[i].size
        if x + w + 2 * PAD > MAXW:
            x = 0; y += shelf; shelf = 0
        pos[i] = (x + PAD, y + PAD)
        x += w + 2 * PAD
        shelf = max(shelf, h + 2 * PAD)
    H = y + shelf
    atlas = Image.new("RGB", (MAXW, H), (74, 76, 82))
    for i, im in enumerate(thumbs):
        im = im.convert("RGB")
        px, py = pos[i]
        w, h = im.size
        atlas.paste(im, (px, py))
        atlas.paste(im.crop((0, 0, w, 1)), (px, py - 1))          # replicated edges
        atlas.paste(im.crop((0, h - 1, w, h)), (px, py + h))
        atlas.paste(im.crop((0, 0, 1, h)), (px - 1, py))
        atlas.paste(im.crop((w - 1, 0, w, h)), (px + w, py))
    return atlas, pos


def make_favicon():
    """A silver X on the archive's dark ground, 64px."""
    im = Image.new("RGB", (64, 64), (11, 12, 16))
    d = ImageDraw.Draw(im)
    for dx in range(-6, 7):
        d.line([(14 + dx, 14), (50 + dx, 50)], fill=(185, 182, 172), width=3)
        d.line([(50 + dx, 14), (14 + dx, 50)], fill=(185, 182, 172), width=3)
    im.save(os.path.join(SITE, "favicon.png"))


def main():
    inv = json.load(open(os.path.join(HERE, "inventory.json")))
    specs = analyse(inv)
    demand, grown = grow_to_target(specs)

    tiles, thumbs = [], []
    for n, s in enumerate(specs):
        tid = f"t{n:03d}"
        bw, bh = s["bw"], s["bh"]
        if s.get("passage"):
            big = render_passage(s["passage"], bw, bh)
        else:
            im = fit_block(autotrim(flatten(Image.open(os.path.join(SRC, s["rel"])))), bw, bh)
            big = ImageOps.fit(im, (bw * CELL_PX, bh * CELL_PX), Image.LANCZOS)
            big = ImageEnhance.Contrast(ImageEnhance.Color(big).enhance(COLOUR_LIFT)
                                        ).enhance(CONTRAST_LIFT)
        big.save(os.path.join(SITE, "tiles", tid + ".jpg"), "JPEG",
                 quality=84, optimize=True, progressive=True)
        th = microfiche(big.resize((bw * THUMB_CELL, bh * THUMB_CELL), Image.LANCZOS))
        thumbs.append(th)
        tiles.append(dict(id=tid, p=s["p"], c=s["c"], k=s["k"], t=s["t"],
                          h=1 if s["hero"] else 0, bw=bw, bh=bh, ty=1 if s["typey"] else 0,
                          l=round(ImageStat.Stat(th).mean[0]),   # at-rest tone, for layout
                          src=s["rel"]))
    n = len(tiles)
    works = {t["src"] for t in tiles}
    print(f"grown to 2×2 for the figure: {grown}")

    atlas, pos = pack_plate(thumbs)
    for t, (sx, sy) in zip(tiles, pos):
        t["sx"], t["sy"] = sx, sy
    atlas.save(os.path.join(SITE, "plate.jpg"), "JPEG", quality=80, optimize=True)
    make_favicon()

    # a stamp that changes whenever the tiles are rebuilt, so browsers don't serve a
    # half-stale mosaic while we are still tuning the crops
    stamp = abs(hash(tuple(sorted(t["id"] + t["src"] for t in tiles))
                     + (CELL_PX, THUMB_CELL, LETTERBOX_KEEP, COLOUR_LIFT, THUMB_MEAN, THUMB_FLOOR, THUMB_CEIL,
                        int(os.path.getmtime(os.path.join(SITE, "plate.jpg")))))) % 10**9

    # manifest.js is the one file whose URL never changed, so a browser could hold a stale
    # copy and then serve stale image URLs from it. Stamp the script tag and the plate
    # preload too.
    idx = os.path.join(SITE, "index.html")
    html = open(idx).read()
    html = re.sub(r'<script src="manifest\.js[^"]*"></script>',
                  f'<script src="manifest.js?v={stamp}"></script>', html)
    html = re.sub(r'href="plate\.jpg[^"]*"', f'href="plate.jpg?v={stamp}"', html)
    open(idx, "w").write(html)

    with open(os.path.join(SITE, "manifest.js"), "w") as f:
        f.write("const TILES=" + json.dumps(tiles, separators=(",", ":")) + ";\n")
        f.write("const LINKS=" + json.dumps(LINKS, separators=(",", ":")) + ";\n")
        f.write(f"const WORKS={len(works)};\nconst CELL_PX={CELL_PX};\n"
                f"const THUMB={THUMB_CELL};\nconst PLATE_W={atlas.width};"
                f"const PLATE_H={atlas.height};\nconst BUILD='{stamp}';\n")
    kb = sum(os.path.getsize(os.path.join(SITE, "tiles", t["id"] + ".jpg")) for t in tiles) // 1024
    tkb = os.path.getsize(os.path.join(SITE, "plate.jpg")) // 1024
    cells = sum(t["bw"] * t["bh"] for t in tiles)
    print(f"{n} works · {cells} grid cells · tiles {kb//1024} MB · plate {tkb} KB ({atlas.width}x{atlas.height})")
    from collections import Counter
    shapes = Counter(f'{t["bw"]}x{t["bh"]}' for t in tiles)
    print("  block shapes:", "  ".join(f"{k}:{v}" for k, v in sorted(shapes.items())))
    for p, c in Counter(t["p"] for t in tiles).most_common():
        print(f"  {c:4}  {p}")


if __name__ == "__main__":
    main()
