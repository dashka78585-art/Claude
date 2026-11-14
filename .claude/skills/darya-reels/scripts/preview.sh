#!/usr/bin/env bash
# Кадр-превью из готового видео в цветах айфона. См. preview.py.  Использование: preview.sh <video> <секунда> <out.jpg> [ширина=540]
exec python3 "$(dirname "$0")/preview.py" "$@"
