#!/bin/bash
# Build the thread's main video (01-main-video.mp4).
# make.sh <opening footage.mp4> <run data folder> <work dir> <out.mp4>
#   opening footage: Anthropic's "Claude Fable 5.2 controls physical robot arms" (YouTube 54Oajk23wbI) at 1080p.
#     Only its first 5.9 s are used. It is not in this repo.
#   run data folder: stages.json, plus <run>-lanes.json and <run>-front.mp4 for cups-02, towel-fold-18
#     and towel-fold-23 (robot-api's demo data).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src=$1; dsk=$2
work=$(mkdir -p "$3" && cd "$3" && pwd)
out=$(cd "$(dirname "$4")" && pwd)/$(basename "$4")

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
python3 -I "$here/prep.py" "$dsk" "$work/data.json"
python3 -I -c "import sys; s = open(sys.argv[1]).read(); d = open(sys.argv[2]).read(); open(sys.argv[3], 'w').write(s.replace('__DATA__', d))" \
  "$here/main-video.html" "$work/data.json" "$work/main-video-built.html"

# Render every frame in headless Chrome and encode with ffmpeg.
node "$here/render.js" "$work/main-video-built.html" video "$out"
