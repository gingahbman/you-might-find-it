#!/bin/bash
# Headless still of the archive.  usage: ./shot.sh out.png [zoom] [panX] [panY]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HERE/sheets/shot.png}"
Z="${2:-1}"; PX="${3:-0}"; PY="${4:-0}"
CACHE="$(mktemp -d)"        # a throwaway cache dir: otherwise Chrome serves the previous build
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=${DPR:-1} \
  --window-size=1600,1000 --allow-file-access-from-files \
  --disk-cache-dir="$CACHE" --disk-cache-size=1 \
  --virtual-time-budget=12000 --screenshot="$OUT" \
  "file://${HERE}/site/index.html?z=${Z}&px=${PX}&py=${PY}&rows=${ROWS:-}&stroke=${STROKE:-}" 2>/dev/null
rm -rf "$CACHE"
echo "$OUT"
