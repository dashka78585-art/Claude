#!/usr/bin/env bash
# Паузы по звуку (Whisper растягивает слова на паузы, поэтому режем по silencedetect).
# Использование: pauses.sh <audio.wav>   → строки "start end duration"
ffmpeg -hide_banner -i "$1" -af "highpass=f=80,silencedetect=noise=-32dB:d=0.22" -f null - 2>&1 \
 | grep -oE "silence_(start|end): [0-9.]+" | paste - - | awk '{printf "%.2f %.2f %.2f\n",$2,$4,$4-$2}'
