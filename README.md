# You Might Find It — The Archive

An interactive archive of 284 works arranged into a single X. At rest the whole thing is a
grey plate and reads as one mark; zooming in blooms it into full colour and resolves it
into the individual pieces. Nothing is drawn — the X exists only where the works are.

**Live:** https://gingahbman.github.io/you-might-find-it/

```
inventory.py   scan the source folders, record size/aspect/exposure  -> inventory.json
prepare.py     the build: sources -> site/tiles, site/plate.jpg, site/manifest.js
projects.py    metadata: project names, links, titles, heroes, exclusions
writing.py     prose sources: .docx -> passages, set as type by prepare.py
audit.py       what got cropped, letterboxed, or reads as a wall of type
contact.py     contact sheets of the sources, for reference
shot.sh        headless still of the finished piece
shot_size.sh   the same at an arbitrary viewport, for responsive checks
site/          the deployed site
```

## Build

```bash
python3 inventory.py && python3 prepare.py
```

Requires Pillow. Sources are expected in `../Microfiche Photos` and fonts in
`../START/fonts`; both can be relocated with `ARCHIVE_SRC` and `ARCHIVE_FONTS`. The source
images are not in this repository — only the processed tiles are.

Deploy is two commands:

```bash
git push origin main
git subtree push --prefix site origin gh-pages
```

---

## The figure

The X is defined on integer cells rather than by testing cell centres against a drawn
shape. Row `r` of the down-right stroke is exactly columns `[r, r+w-1]`; the down-left
stroke is its mirror. Every row steps by exactly one column, so both edges are true 45°
staircases with no stutter, the ends are flat like a letter X, and the figure is symmetric
about both axes by construction — the mirror of stroke A at row `R-1-r` *is* stroke B at
row `r`. Two integers decide everything: the mark is `(R+w-1) × R` cells and the stroke is
`w/√2` cells thick.

Every `(R, w)` that tiles perfectly is scored on how square it sits and how heavy the
stroke reads; the best wins. Currently **42 rows, stroke 8 — 49 × 42 cells, aspect 1.17.**

Because every block sits wholly inside the cell set and every cell is filled, the
silhouette the works make is precisely this shape. `window.__stats` reports `emptyCells`
and `asymmetric`, both computed from the cells the tiles actually cover; both are 0. If the
archive ever changes such that no figure tiles perfectly, the page throws rather than
quietly leaving gaps — adjust `TARGET_CELLS`.

**Slack.** The cell count almost never equals what the works ask for. Growing a 1×1 to 2×2
absorbs three cells and costs nothing, since a 1×1 tile is already square; the odd
remaining cell is absorbed by giving one work a 2×1 and letting it sit whole inside with
ground either side. `TARGET_CELLS` in `prepare.py` is set so the archive already adds up to
nearly the right number, which is why nothing has to be grown at run time — works are
*rendered* at their final size.

**Packing.** Big blocks go down first, largest first, each searching the whole figure from
its own starting point. Walking cells and taking whichever block happens to fit boxes the
awkward shapes out: a 4×2 banner has far fewer homes than a 2×2 and must claim one before
the 2×2s fragment the space.

**Distribution.** Works are sorted by their at-rest tone and reordered with a golden-ratio
stride, so any stretch of the sequence is representative of the whole range. Plain
light/dark alternation is not enough — it deals the extremes first and the mid-tones last,
which puts every pale typeset passage at one end of the walk. Each block size is spread
across the figure independently for the same reason.

## The build pipeline

A square centre-crop of a phone screenshot is a slab of white, so each source goes through:

1. **Flatten** — transparency composited onto the dark ground.
2. **Auto-trim, symmetrically** — the flat border is detected from the corner pixels and
   cropped away. It trims the *same* amount from opposite sides, keeps a square source
   square, and never takes more than a third of a side. Cropping to the content's bounding
   box instead beheads artwork: on a gradient ground the mask comes out lopsided, and the
   crop follows it.
3. **Type gets a small block** — a page grab, a pitch-deck slide or a marketing screenshot
   is unreadable at any size the mosaic can give it. `is_type()` catches them (pale ground,
   fine edges, no colour) and caps them at two cells, so they act as texture rather than
   eating eight cells of the figure. 57 of the 244 image works land here.
4. **Block shapes, not slices** — a work keeps its own proportions and takes as many cells
   as it needs: 1×1, 2×1, 1×3, 4×1, up to four cells long. A 12:1 banner has no square in
   it worth cropping to, so it isn't cropped to one. Nothing is cut into fragments.
5. **Letterbox past the limit** — blocks stop at four cells. Anything more than ~1.2× off
   its block's aspect is padded onto the ground colour and shown whole rather than cropped.
   `LETTERBOX_KEEP` is deliberately generous: exactly one work is cropped at all.
6. **Detail-seeking crop** — for the mild crops that remain, the window with the most edge
   energy wins, not the centre.
7. **Colour lift** — a modest saturation and contrast bump, applied to the full tiles only
   and never to the grey plate.
8. **Two outputs** — a 600px-per-cell colour tile, and a 100px-per-cell grey thumbnail.

## Why the thumbnails are grey and flattened

At rest the piece is one silver plate, and the figure has to read as a solid form from
across the room. Left alone it doesn't: a white product shot beside a black app screenshot
punches holes in the silhouette.

So the thumbnails are an exposure pass, not just small versions. Autocontrast, a 60%
histogram-equalise blend, a gamma shift putting each tile's **median** luminance on a
common target, then a remap into a fixed band (74–236). Median rather than mean: a black
screenshot with one bright logo has a perfectly good mean and still reads as a hole. The
result has a dark-pixel fraction whose median is about 0.06.

All colour lives in the full-size tiles, which is why zooming blooms.

## The writing is set, not screenshotted

Screenshots of prose are grey noise at mosaic scale. The 21 `.docx` pieces in
`Old Writings` are read straight out of their zip (no library) and **set as type** by
`prepare.py` — DM Serif Display over Sora on a paper ground, auto-fitted so the passage
fills its block. They then behave like any other work: blocks, exposure into the plate,
hover labels.

Each piece gives its title plus its opening passage, cut at a sentence boundary, skipping
greetings and email headers. Pieces under ~46 words are shown whole with line breaks
intact, which is how the poems survive. The 19 longer pieces also give a second passage
chosen by hand in `SECOND_PASSAGE`, keyed by the *opening words of the paragraph* rather
than an index, so the selection is legible in the source and survives edits to the
document. `python3 writing.py` prints every passage and reports any key that stopped
matching. 40 passages from 21 pieces.

## Rendering

**Two layers, no CSS filter.** The bloom used to be `filter: grayscale()` on the zooming
layer. Don't put one back: a filtered element is rasterised once and then *scaled*, so
zooming went sharp → blurry → sharp as the browser caught up. The piece is instead two
stacked copies of the mosaic — `#plate` (grey, exposure-corrected) and `#colour` (the full
tiles) — and the render loop animates nothing but `#colour`'s opacity.

**No permanent `will-change` either.** It promotes `#world` to its own composited layer,
which the GPU rasterises once and then magnifies; at ×14 that layer would want roughly
20,000 × 17,000 device pixels on a retina screen, past what Chrome will allocate. It is
added only while the view is moving and dropped a few frames after it settles.

**The view cannot out-run the data.** Tiles hold `CELL_PX` per cell; a retina screen
doubles every CSS pixel and hovering pops a tile another 28% on top. At 460px per cell, max
zoom was asking for up to 843 device pixels out of a 460px tile. Cells are 600px and `maxS`
is capped by `CELL_PX / (TILE × dpr × HOVER_POP)`. On a large display the ceiling arrives
sooner, which is correct. `HOVER_POP` must stay in step with the `:hover` scale in the CSS.

**Type.** The chrome and the typeset tiles share one voice — DM Serif Display over Sora,
self-hosted, subset to the 92 characters the page can display (38 KB for the pair,
preloaded, `font-display:swap`).

## Loading

The grey plate is one spritesheet (`plate.jpg`, ~1.2 MB) rather than 284 thumbnail files,
so first paint is four requests: page, manifest, plate, favicon. Sprites carry a 2px
replicated-edge gutter so fractional `background-position` can't bleed a neighbour in;
letterboxed and grown tiles render the sprite on a clipped inner pane, since `contain` and
`cover` would expose the atlas.

The 22 MB of colour tiles sits behind an `IntersectionObserver` that fires past ×1.02 zoom
and only for what's on screen. The trigger reads the **target** scale (`st.s`), not the
animated one: the piece opens on a pull-back from ×4, so testing the current scale fired
the whole full-resolution load on first paint, for a view about to settle back to the grey
plate anyway.

`manifest.js` carries a `BUILD` stamp appended to every image URL, and `prepare.py` stamps
the `<script src="manifest.js?v=…">` tag too — otherwise the one file whose URL never
changed could be served stale and hand out stale image URLs from inside.

## Interaction

- **Click digs.** Each click sinks the view ×1.7 (`DIG`) centred on the pointer.
- **Links are depth-gated.** A work only becomes openable past ×4.2 (`LINK_AT`) — the third
  scoop. Below that every click digs, so nothing opens by accident while the visitor is
  still taking in the piece. The hover tag teaches the rule: *dig deeper to open* below,
  *click to open* at depth, with the pointer cursor only appearing once opening is armed.
- **Click, not drag.** The same gesture pans, so a click counts only if the pointer moved
  under 9px and was down under 600ms. `linkUnder()` hit-tests with `elementsFromPoint`
  rather than trusting `e.target`, because pointer capture (needed for smooth drags) makes
  the browser fire clicks at the stage rather than the tile beneath the cursor.
- **Touch reveals before it opens.** A finger has no hover, so on a coarse pointer the first
  tap on an armed work shows its name and the second opens it.
- **Keyboard.** Arrows pan, `+`/`−` zoom, `Escape`/`0` reset.
- **Cursor.** A shovel, inline SVG in a data URI, drawn vertically and rotated 45°. It
  appears only on or near the mark: `nearMark()` maps the pointer back through the world
  transform to a grid cell and checks that cell plus a 46px halo, so the hot region is
  X-shaped rather than the mark's bounding box.
- **The invitation.** On a pointer device the shovel cursor is itself the affordance. Touch
  has no equivalent, so on touch screens the plate advertises itself: until the first
  interaction, light runs down all four arms of the X at once, tip to centre — tiles on
  each arm's centre line glint in sequence, the way aisle lights walk you into a cinema.
  It is the plate catching light (a brief brightness/warmth shift per tile), not an
  overlay, and it never plays again after the first touch. Above the mark floats a bare
  line of gold type, *tap to dig*, positioned just off the top row; tapping the words
  performs the first dig, centred on the X. The hint was once hidden below 820px on the
  reasoning that touch explains itself; it does not, and mobile visitors had no indication
  the mark was interactive at all.
- **The depth gauge.** On a phone the counters live in the statement block, which fades
  once you are digging — exactly when depth becomes interesting. So the ×-readout leaves
  the caption and surfaces as its own small gauge opposite Reset, visible only while
  zoomed.
- **Two leads.** The desktop statement keeps "Keep digging. You'll know it when you find
  it.", which its paragraph leans on. The phone drops that paragraph, so its lead speaks
  plainly — "Take a dig around. If something catches your eye, feel free to contact me
  below." — with the counters and the Résumé/Contact links directly under it, embedded or
  not, so "below" is always true.

### Embedding

`?embed=1` suppresses the chrome a host page already provides: the wordmark always, and on
narrow screens the Résumé/Contact links (the site menu has them) with the counters moved to
the space the wordmark vacated, clear of a header's menu button.

Sizing an embed is the host's job, but the piece cooperates: a resize before the first
interaction re-fits to ×1, so a frame the host sizes *after* load doesn't get stuck at
whatever scale the pre-sizing frame implied. After the first interaction a resize preserves
the view instead, because by then there is something worth not disturbing.

## Layout

Three layouts, chosen by the shape of the viewport rather than by device:

| viewport | layout |
|---|---|
| wide | statement in the X's left waist, full chrome |
| narrow **and** portrait (≤820px, aspect ≤ 4/5) | statement stacked under the mark, `#world` nudged up, hint floating above the mark, counters and nav folded into the statement, depth gauge opposite Reset, 44px touch targets |
| short (≤560px tall) | statement narrowed into one clear column beside the mark |

The statement sits vertically centred against the left edge because an X splays to its full
width at top and bottom — the lower-left corner is exactly where a stroke lands. The waist
of an X is always narrow, so the left-middle is clear at every size.

Stacking requires genuinely portrait proportions, not just a narrow width: a squarish
800×810 viewport took the phone layout, stacked the statement below a mark that had no room
above it, and put the text on the figure.

Chrome recedes to 0.11 past the bloom and returns on hover; the controls hold at 0.72.
The entrance is staged — mark, then statement, then chrome — on CSS transition-delays,
which a `body.entered` class clears once the intro is done. Left in place they would also
delay every later fade, and the chrome would take a beat to recede when digging in.

Verified at 1920×1080, 1440×900, 1280×800, 1152×864, 1024×768, 844×390, 820×1180 and
390×844. Note that headless Chrome clamps the viewport to a 500px minimum width — anything
narrower renders at 500 and is cropped, which looks exactly like a broken mobile layout and
isn't. Check phone widths in a real browser.

## Configuration

Everything editable lives in `projects.py`:

| | |
|---|---|
| `PROJECTS` | source folder → display name, category, kind |
| `LINKS` | project → URL. A project with no entry isn't clickable. |
| `TITLES` | source path → title, overriding the filename-derived one |
| `HEROES` | works that get a double-size block |
| `EXCLUDE` | sources left out entirely |
| `RENAME` | filename prefix → nicer title fragment |

`TITLES` exists because filename-derived titles were not merely bland but wrong: the
ELECTION card batches both number from 01, so `jpegs1-01` and `pngs2-01` both became
"Card 01" — 37 labels pointing at two different cards each. All 82 are now named from the
artwork.

Tuning knobs in `prepare.py`: `CELL_PX` (resolution ceiling), `TARGET_CELLS` (decides the
figure's proportions), `LETTERBOX_KEEP`, `COLOUR_LIFT`, and the `THUMB_*` exposure band.
In `index.html`: `DIG`, `LINK_AT`, `HOVER_POP`, `BREATHE`.

## Known gaps

- Eight projects have no `LINKS` entry, so 24 tiles aren't clickable — Two Dots and a Line
  is the largest at nine.
- Maga Bodega has no images and is therefore absent from the archive entirely.
- One Rainbow Cobra source is a near-solid black frame that no exposure pass can save.
- `Quickfire/01-app-icon-512.png` and `02-app-icon-192.png` were the same artwork exported
  twice; both are excluded. Other duplicate exports may exist in the sources.
