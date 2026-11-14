"""Распознавание речи с таймингами слов.
Использование: python3 transcribe.py <audio.wav 16k mono> <out words.json> ["подсказка: термины, через запятую"]
"""
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

wav, out = sys.argv[1], sys.argv[2]
hint = sys.argv[3] if len(sys.argv) > 3 else "Педиатр, ребёнок, грудное вскармливание, ГВ, прикорм, температура, вакцинация."
wf = wave.open(wav)
audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
model = WhisperModel('medium', device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = model.transcribe(audio, language='ru', word_timestamps=True, initial_prompt=hint, vad_filter=True)
res = []
for s in segs:
    res.append({'start': s.start, 'end': s.end, 'text': s.text,
                'words': [{'w': w.word, 's': w.start, 'e': w.end} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
