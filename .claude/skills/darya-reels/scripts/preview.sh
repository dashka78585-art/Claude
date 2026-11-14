#!/usr/bin/env bash
# Кадр-превью из ГОТОВОГО видео, приближённый к тому, как айфон показывает HDR (только для согласования; видео не меняется).
# Использование: preview.sh <video> <секунда> <out.jpg> [ширина=540]
V="$1"; T="$2"; OUT="$3"; WD="${4:-540}"
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$V")
if [ "$TRC" = "arib-std-b67" ]; then
  VF="zscale=pin=bt2020:p=bt709:min=bt2020nc:m=bt709:tin=arib-std-b67:t=arib-std-b67,eq=contrast=1.12:saturation=1.15:gamma=0.95,format=yuv420p,scale=$WD:-1"
else
  VF="scale=$WD:-1"
fi
ffmpeg -v error -y -ss "$T" -i "$V" -frames:v 1 -vf "$VF" "$OUT"
