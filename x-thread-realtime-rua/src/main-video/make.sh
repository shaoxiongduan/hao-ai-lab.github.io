#!/bin/bash
# Build the thread's main video (01-main-video.mp4).
# make.sh <work dir> <out.mp4> [opening footage.mp4] [run data folder]
#   opening footage: defaults to ../../assets/opening/fable52-opening.mp4, the first 6.2 s of Anthropic's
#     "Claude Fable 5.2 controls physical robot arms" (YouTube 54Oajk23wbI, 1080p). Only 5.9 s are used.
#   run data folder: defaults to ../../assets/runs, a copy of robot-api's docs/demos (branch shao/dsk-real):
#     <run>-front.mp4 for cups-02, towel-fold-18 and towel-fold-23, with stages.json and <run>-lanes.json
#     in data/. A flat folder with all seven files also works.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
assets=$here/../../assets
work=$(mkdir -p "$1" && cd "$1" && pwd)
out=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
src=${3:-$assets/opening/fable52-opening.mp4}
dsk=${4:-$assets/runs}
data=$dsk; [ -f "$dsk/stages.json" ] || data=$dsk/data

# Opening: the first 5.9 s of the footage as frames.
mkdir -p "$work/opening"
ffmpeg -v error -y -ss 0 -t 5.9 -i "$src" -vf fps=30 -q:v 2 "$work/opening/f%03d.jpg"

# The three runs' front camera, sped up to match the lanes: <run> <start s> <speed>.
while read -r run ss speed; do
  mkdir -p "$work/res/$run"
  ffmpeg -v error -y -ss "$ss" -i "$dsk/$run-front.mp4" -vf "setpts=PTS/$speed,fps=30,scale=552:-2" -q:v 3 "$work/res/$run/%04d.jpg"
done <<EOF
cups-02 7.0 27
towel-fold-18 7.8 17
towel-fold-23 18.5 60
EOF

# Lane data (the committed data.json is this step's output), then the page with the data inlined.
python3 -I "$here/prep.py" "$data" "$work/data.json"
python3 -I -c "import sys; s = open(sys.argv[1]).read(); d = open(sys.argv[2]).read(); open(sys.argv[3], 'w').write(s.replace('__DATA__', d))" \
  "$here/main-video.html" "$work/data.json" "$work/main-video-built.html"

# Render every frame in headless Chrome and encode with ffmpeg.
node "$here/render.js" "$work/main-video-built.html" video "$out"
