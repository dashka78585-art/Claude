# Субтитры для рилсов — стиль B «Нежный акцент»

Заголовок: Unbounded (верхняя строка) + рукописный Caveat (розовый акцент).
Субтитры: Manrope 800, графит с белым свечением; ключевое слово — Caveat, розовый `#C85A78`.

## Шаги

1. Аудио: `ffmpeg -i in.mov -vn -ac 1 -ar 16000 in.wav`
2. Распознавание (faster-whisper, модель medium, нужен доступ к huggingface.co):
   `python3 transcribe.py in.wav` → `words.json` с таймингами слов.
3. Вычитать текст, разбить на фразы в `projects/<имя>/chunks.py`
   (`(старт, конец, "текст с *ключевым* словом")`), сохранить как `chunks.json`.
4. Отредактировать заголовок в `overlay.html` (`#head`).
5. `node mk.js` → PNG-слои в `render/` (+ `render/list.txt` для concat).
6. Склейка слоёв в дорожку и наложение на видео — см. команду ffmpeg в истории сессии:
   `eq=saturation=1.1` без тонмаппинга (iPhone HLG HDR так выглядит естественнее), x264 CRF 18, звук копируется.

Готовые видео в репозиторий не коммитятся (`video/` в `.gitignore`).
Шрифты — Google Fonts (OFL) через @fontsource.
