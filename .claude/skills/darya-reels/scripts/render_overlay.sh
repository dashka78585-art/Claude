#!/usr/bin/env bash
# Анимированная графика (заголовок, субтитры, вставки) в Remotion → прозрачный ProRes 4444.
# Использование: render_overlay.sh <project.json> <fonts_dir с платными шрифтами> <out overlay.mov> [--seconds N]
set -euo pipefail
K="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$(realpath "$1")"; FONTS="$(realpath "$2")"; OUT="$(realpath -m "$3")"; shift 3
R="$K/remotion"
[ -d "$R/node_modules" ] || (cd "$R" && npm install --silent)
mkdir -p "$R/public/fonts"
cp "$K"/fonts/*.ttf "$R/public/fonts/"
for f in stolzl_regular.otf stolzl_bold.otf Peach_Cream.otf; do
  [ -f "$FONTS/$f" ] || { echo "нет шрифта $FONTS/$f — попросить у Дарьи"; exit 1; }
  cp "$FONTS/$f" "$R/public/fonts/"
done
PROPS="$(mktemp --suffix=.json)"
python3 "$K/scripts/render.py" "$PROJ" - - --props-out "$PROPS" "$@"
# Remotion по умолчанию качает свой браузер с remotion.media (сеть сессии его не пускает) — берём предустановленный.
BROWSER="${REMOTION_BROWSER:-$(ls /opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell 2>/dev/null | head -1)}"
cd "$R"
npx remotion render src/index.ts Overlay "$OUT" --props="$PROPS" \
  --codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png --log=error ${BROWSER:+--browser-executable="$BROWSER"}
rm -f "$PROPS"
echo "графика: $OUT"
