# The Archive — built from the real images

This is `START/index_x_neat.html` rebuilt with your actual work instead of the 33 sample
photos. Open `site/index.html` in a browser — no server needed.

## What's here

```
inventory.py     scans "Microfiche Photos", records every image's size/exposure -> inventory.json
contact.py       contact sheets of the SOURCE images            -> sheets/sheet_*.png
projects.py      the metadata table you edit: folder -> project name, category, heroes, titles
writing.py       the writing as works: Old Writings .docx -> opening + a hand-picked passage
audit.py         what got cropped / letterboxed / reads as type, and the saturation spread
prepare.py       the cleanup pipeline: source images -> site/tiles + site/thumbs + manifest.js
shot.sh          headless still of the finished piece           -> sheets/*.png
site/index.html  the piece itself
```

Rebuild after changing anything:

```bash
python3 inventory.py && python3 prepare.py
```

## The cleanup pipeline (`prepare.py`)

The hard part isn't the mosaic, it's that a square centre-crop of a phone screenshot is a
slab of white. Every source image goes through:

1. **Flatten** — transparency composited onto the archive's dark ground (the 75 ELECTION
   card PNGs and every app icon have alpha).
2. **Auto-trim, symmetrically** — the flat border is detected from the corner pixels and
   cropped away, which rescues the product shots and store screenshots (mostly margin).
   It trims the *same* amount from opposite sides, keeps a square source square, and never
   takes more than a third of a side. The naive version — crop to the content's bounding
   box — beheads artwork: on a ground that's a gradient rather than a flat colour the mask
   comes out lopsided, and it took the ears off the Feelabit rabbit and halved the heart.
3. **Type gets a small block** — a page grab, a pitch-deck slide or a marketing screenshot
   is unreadable at any size the mosaic can give it. `is_type()` catches them (pale ground,
   fine edges, no colour) and caps them at two cells, so they act as texture instead of
   eating eight cells of the X. 57 of the 244 image works land here.
4. **Block shapes, not slices** — a work keeps its own proportions and takes as many grid
   cells as it needs: 1×1, 2×1, 1×3, 4×1, up to four cells long. A 12:1 banner or a phone
   screenshot has no square in it worth cropping to, so it isn't cropped to one. Nothing
   is ever cut into fragments.
5. **Letterbox past the limit** — blocks stop at four cells, so a 12:1 banner still
   doesn't fit one. Anything more than ~1.2× off its block's aspect is padded onto
   the ground colour and shown whole rather than cropped. `LETTERBOX_KEEP` is deliberately
   generous: exactly one work in the whole archive is now cropped at all.
6. **Detail-seeking crop** — for the mild crops that remain, the window with the most edge
   energy wins, not the centre. A logo in the corner of a frame stays in shot.
7. **Colour lift** — a modest saturation and contrast bump, applied to the full tiles
   only and never to the grey plate, so the bloom actually reads as a bloom.
8. **Two outputs per work** — a 600px-per-cell full-colour `tiles/` file, and a
   100px-per-cell `thumbs/` file.

## The writing is set, not screenshotted

All of it comes from the 21 `.docx` pieces in **Old Writings**, and nowhere else.

`writing.py` opens each one straight out of its zip (no library), and takes two things:

- **the opening** — title plus enough of the first real paragraph to stand on its own, cut
  at a sentence boundary. It skips greetings and email headers, so *sounds of sonder* opens
  on "It's me. I'm not really sure how to begin this…" rather than "Hey,". Pieces under ~46
  words are shown whole, line breaks intact, which is how the poems survive.
- **a second passage** from further in, for the 19 pieces long enough to have one. These are
  chosen by hand in `SECOND_PASSAGE`, keyed by the *opening words of the paragraph* rather
  than an index — so you can see at a glance which passage is meant, and it survives edits
  to the document. Run `python3 writing.py` to print every passage and to be told about any
  key that has stopped matching.

40 passages from 21 pieces. `prepare.py` sets them as type on a paper ground — DM Serif
Display over Sora, auto-fitted so the passage fills its block — and writes them out as
ordinary tiles: they get blocks, they get exposure-corrected into the plate, they're
labelled on hover. A short line takes a wide 2×1 and is set large; a paragraph takes a 2×2.
Both tiles from a piece carry its title and its word count, so they read as two pages from
the same work.

To change a passage, edit the phrase in `SECOND_PASSAGE` and rebuild. To drop one, delete
the entry.

## Why the thumbnails are grey and flattened

At rest the whole piece is one silver plate, and the X has to read as a solid form from
across the room. Left alone it doesn't: a white product shot next to a black app
screenshot punches holes in the silhouette.

So the thumbnails aren't just small versions — they're an exposure pass. Autocontrast,
a 60% histogram-equalise blend, then a gamma shift that puts each tile's **median**
luminance on the same target, then a remap into a fixed band (74–236). Median, not mean:
a black screenshot with one bright logo has a perfectly good mean and still reads as a
hole. The result is a mosaic with a dark-pixel fraction whose median is about 0.06.

The colour lives entirely in the full-size tiles, which is why zooming blooms.

## Two layers, no CSS filter

The bloom used to be a `filter: grayscale()` on the zooming layer. Don't put one back: a
filtered element gets rasterised once and then *scaled*, so zooming went sharp → blurry →
sharp as the browser caught up and re-rendered it.

Instead the piece is two stacked copies of the mosaic — `#plate` (the grey thumbnails,
already exposure-corrected) and `#colour` (the full tiles) — and the render loop animates
nothing but `#colour`'s opacity. No filter anywhere, so the browser rasterises at the real
scale the whole way in. It also cross-dissolves properly, which a filter never did.

## Sharpness at deep zoom

Two things were making zoomed-in tiles blurry, and both are the same mistake in different
clothes: letting the browser cache a raster and then scale it.

- **`will-change` on the zooming layer.** It promotes `#world` to its own composited layer,
  which the GPU rasterises once and then magnifies — at ×14 that layer would want something
  like 20,000 × 17,000 device pixels on a retina screen, past what Chrome will allocate. It
  is now added only while the view is actually moving and dropped a few frames after it
  settles (`settle()` in the render loop), so panning stays cheap and standing still is
  sharp. Same reason there is no CSS `filter` anywhere. Don't reintroduce either.
- **Zooming past the pixels that exist.** Tiles hold `CELL_PX` per cell; a retina screen
  doubles every CSS pixel and hovering pops a tile another 28% on top. At 460px per cell,
  max zoom on a retina laptop was asking for up to 843 device pixels out of a 460px tile.
  Cells are now 600px, and `maxS` is capped by `CELL_PX / (TILE × dpr × HOVER_POP)` so the
  view can never out-run the data. On a large display you reach the ceiling sooner, which
  is correct — the tiles are already enormous by then.

`HOVER_POP` in the script must stay in step with the `:hover` scale in the CSS.

## Load behaviour

The grey plate is now ONE spritesheet (`plate.jpg`, ~1.2 MB) instead of 284 thumbnail
files — first paint is 4 requests: page, manifest, plate, favicon. Sprites carry a 2px
replicated-edge gutter so fractional background-position can never bleed a neighbour in;
letterboxed and grown tiles render the sprite on a clipped inner pane, since contain/cover
keywords would expose the atlas. The ~1.2 MB plate paints the whole X at once. The 24 MB of full tiles is
behind an `IntersectionObserver` that only fires past ×1.02 zoom, and only for what's on
screen — so the detail is already decoded before the colour starts to show at ×1.03, and
costs nothing until someone actually leans in.

The trigger reads the **target** scale (`st.s`), not the animated one. The piece opens on a
pull-back from ×4, so testing the current scale fired the whole full-resolution load on
first paint — tens of megabytes fetched before the visitor had done anything, for a view
that was about to settle back to the grey plate anyway.

`manifest.js` carries a `BUILD` stamp appended to every image URL, and `prepare.py` stamps
the `<script src="manifest.js?v=…">` tag in `index.html` too — otherwise the one file whose
URL never changed could be served stale and hand out stale image URLs from inside.

## The page around it

- **Links.** `LINKS` in `projects.py` maps a project's display name to a URL; `prepare.py`
  writes it into the manifest and every tile from a linked project gets `.link` and a
  `data-href`. Clicking one opens it in a new tab — but only past the depth gate (`LINK_AT`, ×4.2 —
  the third scoop), so nobody can open a work by accident while still taking in the visual;
  below the gate every click digs and the hover tag says "dig deeper to open". And only
  if it really was a click: the same gesture drags the mosaic, so the handler checks the
  pointer moved under 6px and was down under 600ms. A linked tile suppresses the
  double-click dive rather than doing both, and a second open inside 500ms is ignored, so
  double-clicking can't open two tabs. Hover shows `↗ OPEN` and the cursor turns to a
  pointer. A project with no `LINKS` entry simply isn't clickable.
- **Cursor.** A shovel, inline SVG in a data URI, drawn vertically and rotated 45°. It costs
  nothing at runtime — a CSS cursor is decoded once, not a script chasing the pointer. Dark
  outer stroke so it survives the black ground, the grey plate and a white product shot;
  `crosshair` fallback if the data URI is ever rejected. The blade shape matters at 30px: a
  spear point reads as an ordinary arrow and a flat-edged blade reads as a mallet, so it is
  a broad rounded blade with shoulders.
  It appears **only on or near the mark** — `nearMark()` maps the pointer back through the
  world transform to a grid cell and checks that cell plus a 46px halo, so the hot region is
  X-shaped rather than the mark's bounding box, and the empty wedges between the arms give
  the ordinary pointer. A dozen arithmetic ops per pointermove, no layout reads, and the
  class only changes when the answer does.
- **The statement** replaced the per-project tally, and fades on zoom exactly as the tally
  did. `Résumé` and `Contact` sit below it and never fade.
- **Where the statement sits is not arbitrary.** It is vertically centred against the left
  edge, because an X splays to its full width at the top and bottom — the lower-left corner
  is exactly where a stroke lands, and the text was running under the arm at 1280×800. The
  waist of an X is always narrow, so the left-middle is clear at every viewport size.

## Sizes it has to survive

Three layouts, by shape of viewport rather than by device:

| viewport | layout |
|---|---|
| wide (>820px) | statement in the X's left waist, full chrome |
| narrow (≤820px) | statement stacked under the mark, `#world` nudged up 9vh, hint hidden, buttons 44px, `+`/`−` dropped under 420px |
| short (≤560px tall) | phone on its side or a squat window: statement narrowed to one clear column beside the mark, everything else shrunk |

Type is `clamp()`d so it scales between those. The mark takes 94% of the short side on a
phone and 80% on a desktop — a phone is width-limited with height to spare, a desktop needs
the room for chrome.

Verified at 1920×1080, 1440×900, 1280×800, 1152×864, 1024×768, 844×390 and 820×1180.

**Careful with headless Chrome for this**: it clamps the viewport to a 500px minimum width,
so `--window-size=390,844` renders at 500×757 and crops — which looks exactly like a broken
mobile layout and isn't. Check phone widths in a real browser. `shot_size.sh` says so too.

## The front door

- **Meta/social**: description, og:title/description/image (1200×630 `og.jpg`, rendered
  from the page itself), twitter:card, canonical, theme-color, `favicon.png`. Two absolute
  URLs are marked `UPDATE-AT-DEPLOY` in the head.
- **Semantics/a11y**: the wordmark is an `h1`; zoom buttons have aria-labels; the stage has
  a `role="img"` description; focus-visible outlines on nav and buttons.
- **Keyboard**: arrows pan, `+`/`−` zoom, `Escape`/`0` reset.
- **Reduced motion**: no opening pull-back, no idle breathing, no tile transitions.
- **Ambient breathing**: until first interaction the mark swells ±1.2% on a 9s period, then
  stops for good. `BREATHE=false` at the top of the script kills it.

## Layout — how the X is made exact

`site/index.html`. The rule is that the silhouette the photos make *is* the figure, so the
figure is defined on whole cells and every cell is filled. Nothing is drawn, nothing is
left empty, nothing overhangs.

- **Integer geometry, true 45°.** Row `r` of the down-right stroke is exactly columns
  `[r, r+w-1]`; the down-left stroke is its mirror. Every row steps by exactly one column,
  so both edges are clean staircases with no stutter, the tops and bottoms are flat like a
  letter X, and the figure is symmetric about both axes by construction — the mirror of
  stroke A at row `R-1-r` *is* stroke B at row `r`. Two integers, `R` and `w`, decide
  everything: the mark is `(R+w-1) × R` cells and the stroke is `w/√2` cells thick.
- **The figure is searched, not chosen.** Every `(R, w)` that tiles perfectly is scored on
  how square it sits and how heavy the stroke reads, and the best wins. Currently 42 rows,
  stroke 8 — 49 × 42 cells, aspect 1.17.
- **Slack has to go somewhere, and it isn't a hole.** The cell count almost never equals
  what the works ask for. Growing a 1×1 to 2×2 absorbs three cells and costs nothing (a
  1×1 tile is already square); the odd remaining cell is absorbed by giving one work a 2×1
  and letting it sit whole inside with ground either side. `TARGET_CELLS` in `prepare.py`
  is set so the archive already adds up to nearly the right number, which is why the page
  currently has to grow nothing at run time — the works are *rendered* at their final size.
- **Big blocks first, largest first, each searching the whole figure** from its own
  starting point. Walking cells and taking whichever block happens to fit boxes the awkward
  shapes out: a 4×2 banner has far fewer homes than a 2×2 and must claim one before the
  2×2s fragment the space.
- **Tone is scattered, not banded.** Works are sorted by their at-rest tone and then
  reordered with a golden-ratio stride, so any stretch of the sequence is representative of
  the whole range. Plain light/dark alternation is not enough — it deals the extremes first
  and the mid-tones last, which put every pale typeset passage at one end of the walk.
  Each block size is spread across the figure independently for the same reason.
- **It checks itself.** `window.__stats` reports `emptyCells` and `asymmetric`, both
  computed from the cells the tiles actually cover. Both are 0. If the archive ever changes
  so that no figure tiles perfectly, the page throws rather than quietly leaving gaps —
  adjust `TARGET_CELLS`.

Deep link / still: `site/index.html?z=5&px=-220&py=-160`. `?rows=42&stroke=8` forces a
particular figure, which is how the weights were compared.

## Known rough edges

- **Maga Bodega is no longer in the archive.** It's a full-length play with no images
  attached to it, so quotes were its only presence; 23 projects are now 22. If you want it
  back, either add an image for it or give it its own entry — it needs a source of some kind.
- **Old Writings is now 40 of the 284 works**, second only to ELECTION.
- **ELECTION** is 82 of the 284 works, a third of the whole piece. **CampSorted** (12) is
  white slides with small type — the weakest material in the set. Nothing has been cut.
- Both Quickfire app icons are excluded (`EXCLUDE` in `projects.py`) — off-brand, and the
  two files were the same artwork exported twice anyway. That's the place to drop anything
  else you don't want in the mark.
- The 75 ELECTION cards are labelled `Card 01…39` from their filenames; their real names
  (THE SAGE, MONK-EY, LETDOWN LARRY…) are legible in `sheets/sheet_03.png` and would have
  to be typed into a lookup table.
- The "kindness steers your ship" line now appears twice: once as your original screenshot
  (small, as type) and once set properly. Delete the entry in `writing.py` or the source
  image, whichever you prefer.
- `writing.py`'s `QUOTES` list is hand-picked and short. Every project's `EXCERPTS.md` has
  more in it worth setting.
- `audit.py` reports what got cropped, what got letterboxed, what reads as type, and the
  saturation spread. Run it after any change to `prepare.py`.
