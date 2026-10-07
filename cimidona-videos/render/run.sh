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
  node render.mjs $V.html $W/timing.json --stills "$ARG" $W/stills
  cd $W/stills && montage -mode concatenate -tile 6x $(ls -v *.jpg) -resize 360x -quality 80 ../sheet.jpg 2>/dev/null || convert $(ls -v *.jpg | head -6) -resize 360x +append ../sheet.jpg
  exit 0
fi
node render.mjs $V.html $W/timing.json $W/video.mp4 30
ffmpeg -y -loglevel error -i $W/video.mp4 -i $W/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart $W/cimidona_$V.mp4
ls -la $W/cimidona_$V.mp4
if [ -n "$UPLOAD" ]; then curl -sS -f -X PUT -H "Content-Type: video/mp4" --data-binary @$W/cimidona_$V.mp4 "$UPLOAD" -o /dev/null -w "upload %{http_code}\n"; fi
