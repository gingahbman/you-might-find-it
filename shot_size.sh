#!/bin/bash
# usage: ./shot_size.sh out.png WIDTH HEIGHT [dpr]
# NOTE: headless Chrome clamps the viewport to a 500px minimum width. Anything narrower
# renders at 500 and is then cropped, which is not what a phone does. Use a real browser
# (the preview pane) to check mobile.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="$(mktemp -d)"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --force-device-scale-factor="${4:-1}" \
  --window-size="$2,$3" --allow-file-access-from-files \
  --disk-cache-dir="$CACHE" --disk-cache-size=1 \
  --virtual-time-budget=25000 --screenshot="$1" \
  "file://${HERE}/site/index.html?z=1" 2>/dev/null
rm -rf "$CACHE"
