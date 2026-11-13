#!/bin/bash
# retime.sh <src.mp4> <src speed> <new speed> <dash start> <dash end> <summary start> <dash overlay.png> <summary overlay.png> <out.mp4>
set -euo pipefail
src=$1; s0=$2; s1=$3; a=$4; b=$5; c=$6; ovd=$7; ovs=$8; out=$9
lenA=$(python3 -I -c "print(round(($b-$a)*$s0/$s1, 3))")
off=$(python3 -I -c "print(round($lenA-0.3, 3))")
ffmpeg -v error -y -i "$src" -i "$ovd" -i "$ovs" -filter_complex "\
[0:v]split[s1][s2];\
[s1]trim=start=$a:end=$b,setpts=(PTS-STARTPTS)*$s0/$s1,fps=30,settb=AVTB[a0];[a0][1:v]overlay[a];\
[s2]trim=start=$c:end=$(python3 -I -c "print($c+4)"),setpts=PTS-STARTPTS,fps=30,settb=AVTB[b0];[b0][2:v]overlay[b];\
[a][b]xfade=transition=fade:duration=0.3:offset=$off,format=yuv420p[v]" \
  -map "[v]" -an -c:v libx264 -preset slow -crf 20 -movflags +faststart "$out"
ffprobe -v error -show_entries format=duration,size -of compact "$out"
