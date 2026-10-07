#!/usr/bin/env bash
# Runs inside the Higgsfield sandbox.
#   bash run.sh <video_id> [stills "t1,t2,..."] [upload_url]
# Clones the project branch, fetches assets, builds audio+timing, renders, muxes.
set -euo pipefail
V=$1; MODE=${2:-full}; ARG=${3:-}; UPLOAD=${4:-}
BR=claude/happy-faraday-sxh5rd
cd /home/user
if [ ! -d repo ]; then git clone -q --depth 1 -b $BR https://github.com/yousefawad15/maison-amira.git repo; else (cd repo && git fetch -q --depth 1 origin $BR && git reset -q --hard FETCH_HEAD); fi
P=/home/user/repo/cimidona-videos
W=/home/user/work/$V; mkdir -p $W
[ -f $P/assets/gen/box_angle.png ] || python3 $P/render/fetch_assets.py $P
[ -f $W/timing.json ] && [ "${REBUILD_AUDIO:-0}" = 0 ] || python3 $P/render/build_audio.py $P $V $W
export NODE_PATH=${NODE_PATH:-$(npm root -g)}
cd $P/render
if [ "$MODE" = stills ]; then
  if [[ "$ARG" == auto* ]]; then
    ARG=$(python3 -c "import json;T=json.load(open('$W/timing.json'))['total'];n=${ARG#auto:};print(','.join(f'{(i+0.5)*T/n:.2f}' for i in range(n)))")
  fi
  rm -rf $W/stills
  node render.mjs $V.html $W/timing.json --stills "$ARG" $W/stills
  python3 - "$W" <<'EOF'
import glob, re, sys
from PIL import Image
W = sys.argv[1]
fs = sorted(glob.glob(f'{W}/stills/t*.jpg'), key=lambda f: float(re.search(r't([\d.]+)\.jpg', f).group(1)))
w, h = 300, 533
for part in range(0, len(fs), 9):
    sub = fs[part:part + 9]
    sheet = Image.new('RGB', (w * len(sub), h), 'white')
    for i, f in enumerate(sub):
        sheet.paste(Image.open(f).resize((w, h)), (i * w, 0))
    sheet.save(f'/home/user/sheet_{W.split("/")[-1]}_{part // 9}.jpg', quality=80)
EOF
  exit 0
fi
node render.mjs $V.html $W/timing.json $W/video.mp4 30
ffmpeg -y -loglevel error -i $W/video.mp4 -i $W/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart $W/cimidona_$V.mp4
ls -la $W/cimidona_$V.mp4
if [ -n "$UPLOAD" ]; then curl -sS -f -X PUT -H "Content-Type: video/mp4" --data-binary @$W/cimidona_$V.mp4 "$UPLOAD" -o /dev/null -w "upload %{http_code}\n"; fi
