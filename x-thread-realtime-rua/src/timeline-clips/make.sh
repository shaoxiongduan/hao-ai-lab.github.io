#!/bin/bash
# Render the blog's three timeline videos (content/blogs/realtime-rua/img/<run>-timeline-<speed>x.mp4), which the
# thread's clips are cut from.
# make.sh <out dir> [run ...]     runs default to cups-02 towel-fold-18 towel-fold-23
# Needs a Python with requirements.txt installed (set PYTHON to it), ffmpeg with libx264 (or set FFMPEG), and FriBiDi
# (brew install fribidi) so Pillow lays text out with raqm, as in the published videos.
set -euo pipefail
export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-/opt/homebrew/lib:/usr/local/lib}"   # macOS: where Pillow finds FriBiDi
here=$(cd "$(dirname "$0")" && pwd)
out=$(mkdir -p "$1" && cd "$1" && pwd); shift
runs=${*:-cups-02 towel-fold-18 towel-fold-23}
for r in $runs; do
  OUT="$out" "${PYTHON:-python3}" "$here/render.py" "$r"
done
