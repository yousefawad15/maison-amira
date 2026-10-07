#!/usr/bin/env bash
# Local render (no Higgsfield). Needs: ffmpeg, node + global playwright, python3 numpy/PIL.
#   bash render/render_local.sh v1 [stills auto:N]
# Voiceover clips must already exist in audio/<vid>/ (render/tts_gemini.py).
set -euo pipefail
V=$1; MODE=${2:-full}; ARG=${3:-}
P=$(cd "$(dirname "$0")/.." && pwd)
W=$P/work/$V; mkdir -p $W $P/out
[ -f $P/assets/gen/box_angle.png ] || python3 $P/render/make_cutouts.py $P
if [[ $V == v3 || $V == v4 ]]; then
  for k in 1 2 3 4 5; do [ -f $P/assets/gen/${V}_s$k.jpg ] || python3 $P/render/fetch_assets.py $P $V; done
fi
python3 $P/render/build_audio.py $P $V $W
export NODE_PATH=${NODE_PATH:-$(npm root -g)}
cd $P/render
if [ "$MODE" = stills ]; then
  ARG=$(python3 -c "import json;T=json.load(open('$W/timing.json'))['total'];n=${ARG#auto:};print(','.join(f'{(i+0.5)*T/n:.2f}' for i in range(n)))")
  rm -rf $W/stills; node render.mjs $V.html $W/timing.json --stills "$ARG" $W/stills
  exit 0
fi
node render.mjs $V.html $W/timing.json $W/video.mp4 30
ffmpeg -y -loglevel error -i $W/video.mp4 -i $W/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart $P/out/cimidona_$V.mp4
ls -la $P/out/cimidona_$V.mp4
