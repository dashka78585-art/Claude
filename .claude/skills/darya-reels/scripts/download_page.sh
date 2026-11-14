#!/usr/bin/env bash
# Готовит страницу для сохранения видео на телефон: режет файл на части ≤14 МБ (лимит Artifact на бинарный файл 15 МБ)
# и пишет index.html, который склеивает части и вызывает capability `downloads`.
# Использование: download_page.sh <video.mp4> <out_dir> "<Заголовок страницы>"
set -euo pipefail
VID="$1"; OUT="$2"; TITLE="${3:-Скачать видео}"; NAME=$(basename "$VID")
mkdir -p "$OUT"; rm -f "$OUT"/part*.mp4
split -b 14000000 -d -a 1 "$VID" "$OUT/part"
for f in "$OUT"/part?; do mv "$f" "$f.mp4"; done
N=$(ls "$OUT"/part*.mp4 | wc -l)
sed -e "s/__N__/$N/" -e "s/__TITLE__/$TITLE/g" -e "s/__NAME__/$NAME/" "$(dirname "$0")/../templates/download.html" > "$OUT/index.html"
[ "$(cat "$OUT"/part*.mp4 | md5sum | cut -d' ' -f1)" = "$(md5sum "$VID" | cut -d' ' -f1)" ] && echo "частей: $N, склейка совпадает с исходником"
