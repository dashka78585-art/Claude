"""Dolby Vision (профиль 8.4, айфон): извлечь RPU из исходника и оставить только кадры, которые остались после склеек.
Айфон показывает HDR-видео по этим метаданным; без них ролик на телефоне выглядит площе и бледнее исходника (урок 14.11.2026).

Использование: python3 dovi_rpu.py <src.hevc (Annex B)> <keep.json — индексы оставленных кадров> <out_rpu.bin>
              python3 dovi_rpu.py --inject <encoded.hevc без B-кадров> <rpu.bin> <out.hevc>
Пишет RPU в формате x265 (--dolby-vision-rpu): каждый RPU — 00 00 00 01 + NAL типа 62, по одному на кадр, в порядке показа.
Требует исходник без B-кадров (у айфона has_b_frames=0) — тогда порядок декодирования = порядок показа.
"""
import json, re, sys


def extract(src, keep_path, out):
    data = open(src, 'rb').read()
    starts = [m.start() for m in re.finditer(b'\x00\x00\x01', data)]
    rpus, cur_has_vcl, pending = [], False, None
    frames = []           # RPU (или None) для каждого кадра
    for i, s in enumerate(starts):
        nal = data[s + 3: (starts[i + 1] if i + 1 < len(starts) else len(data))]
        nal = nal.rstrip(b'\x00') if i + 1 < len(starts) else nal
        t = (nal[0] >> 1) & 0x3F
        if t < 32:                                   # VCL — начало/продолжение кадра
            first_slice = nal[2] & 0x80              # first_slice_segment_in_pic_flag
            if first_slice:
                frames.append(None)
        elif t == 62 and frames:                     # Dolby Vision RPU относится к текущему кадру
            frames[-1] = nal
    missing = sum(f is None for f in frames)
    keep = json.load(open(keep_path))
    with open(out, 'wb') as f:
        for k in keep:
            f.write(b'\x00\x00\x00\x01' + frames[k])
    print(f'кадров в исходнике: {len(frames)}, без RPU: {missing}, записано RPU: {len(keep)}')


def inject(hevc_in, rpu_bin, hevc_out):
    """Вставить RPU (по одному на кадр, в порядке показа) последним NAL каждого кадра.
    Поток должен быть без B-кадров (x265 bframes=0), чтобы порядок декодирования совпадал с порядком показа."""
    def nals(buf):
        st = [m.start() for m in re.finditer(b'\x00\x00\x01', buf)]
        for i, s in enumerate(st):
            n = buf[s + 3:(st[i + 1] if i + 1 < len(st) else len(buf))]
            if i + 1 < len(st): n = n.rstrip(b'\x00')
            yield n
    rpus = list(nals(open(rpu_bin, 'rb').read()))
    aus, cur, has_vcl = [], [], False
    for n in nals(open(hevc_in, 'rb').read()):
        t = (n[0] >> 1) & 0x3F
        starts_au = t in (32, 33, 34, 35, 39) or (t < 32 and n[2] & 0x80)
        if has_vcl and starts_au:
            aus.append(cur); cur, has_vcl = [], False
        cur.append(n); has_vcl |= t < 32
    if cur: aus.append(cur)
    if len(aus) != len(rpus):
        sys.exit(f'кадров {len(aus)} ≠ RPU {len(rpus)} — Dolby Vision не перенесён')
    with open(hevc_out, 'wb') as f:
        for au, r in zip(aus, rpus):
            for n in au + [r]:
                f.write(b'\x00\x00\x00\x01' + n)
    print(f'Dolby Vision: RPU вставлены в {len(aus)} кадров')


if __name__ == '__main__':
    if sys.argv[1] == '--inject': inject(*sys.argv[2:5])
    else: extract(*sys.argv[1:4])
