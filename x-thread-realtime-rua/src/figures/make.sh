#!/bin/bash
# Crop the thread's three figures (02, 03, 04) from the blog page, without captions.
# make.sh <site base, e.g. http://localhost:1313 from `hugo server`> <out dir>
# The number before each name is the figure's index on the page (Figure N is index N-1).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$(mkdir -p "$2" && cd "$2" && pwd)
node "$here/figcrop.js" "$1" "$out" "0:02-benchmark-vs-real-robot,4:03-merged-round-trips,9:04-pipelining"
