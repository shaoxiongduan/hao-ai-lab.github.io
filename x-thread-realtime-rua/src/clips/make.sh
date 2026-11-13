#!/bin/bash
# Make the thread's two clips (05 and 06) from the blog's timeline videos: re-time them to about 1 min
# and relabel them (speed pill, "actions" / "WAITING" lanes, summary card) with transparent overlays.
# make.sh <out dir>
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
img="$here/../../../content/blogs/realtime-rua/img"
out=$(mkdir -p "$1" && cd "$1" && pwd)

node "$here/ovshot.js" "$here/overlay.html" "mode=dash&speed=3.5×%20speed" "$out/dash-cup.png"
node "$here/ovshot.js" "$here/overlay.html" "mode=dash&speed=8×%20speed" "$out/dash-towel.png"
node "$here/ovshot.js" "$here/overlay.html" "mode=sum" "$out/sum.png"

# retime.sh <src> <src speed> <new speed> <run view start> <run view end> <summary start> <overlays> <out>
"$here/retime.sh" "$img/cups-02-timeline-2.5x.mp4" 2.5 3.5 3.05 85.8 86.6 \
  "$out/dash-cup.png" "$out/sum.png" "$out/05-cup-game-3.5x.mp4"
"$here/retime.sh" "$img/towel-fold-23-timeline-3x.mp4" 3 8 3.05 165.2 166.1 \
  "$out/dash-towel.png" "$out/sum.png" "$out/06-crumpled-towel-8x.mp4"
