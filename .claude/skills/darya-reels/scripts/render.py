"""Монтаж: вырезка пауз, смены плана и наезды, заголовок на хуке, анимированные субтитры.
Цвет исходника не трогается: кадры обрабатываются в 10 бит, метки цвета копируются из исходника.

Использование:
  python3 render.py <project.json> <layers_dir|overlay.mov> <out.mp4> [--seconds N]
      layers_dir  — PNG-слои из overlays.js (статичные, простая анимация);
      overlay.mov — прозрачная графика из Remotion (ProRes 4444), уже по смонтированному таймлайну.
  python3 render.py <project.json> - - --props-out props.json [--seconds N]
      только посчитать таймлайн и записать props для Remotion (время субтитров/заголовка после вырезки пауз).
  --seconds N — быстрый тест первых N секунд исходника.
Время в project.json — по исходному видео (секунды).
"""
import json, subprocess, sys
import numpy as np, cv2
from PIL import Image

proj, LAY, OUT = sys.argv[1:4]
LIMIT = float(sys.argv[sys.argv.index('--seconds') + 1]) if '--seconds' in sys.argv else None
P = json.load(open(proj))
SRC = P['src']

# ---------- исходник ----------
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
     'stream=width,height,r_frame_rate,nb_read_packets,color_transfer,color_primaries,color_space', '-of', 'json', SRC],
     capture_output=True, text=True).stdout)['streams'][0]
W, H = pr['width'], pr['height']
assert (W, H) == (1080, 1920), f'ожидается вертикальное 1080x1920, а не {W}x{H}: сначала приведите исходник'
num, den = map(int, pr['r_frame_rate'].split('/')); FPS = num / den
NSRC = int(pr['nb_read_packets'])
HLG = pr.get('color_transfer') == 'arib-std-b67'
TRC = pr.get('color_transfer', 'bt709'); PRIM = pr.get('color_primaries', 'bt709'); MAT = pr.get('color_space', 'bt709')
if NSRC == 0: sys.exit('не удалось прочитать кадры')

# ---------- вырезка ----------
CUTS = [(a + 0.06, b - 0.08) for a, b in P.get('cuts', [])]     # оставляем 60 мс до и 80 мс после паузы
keep = [i for i in range(NSRC) if not any(a <= i / FPS < b for a, b in CUTS)]
if LIMIT: keep = [i for i in keep if i / FPS < LIMIT]
newt = {i: k / FPS for k, i in enumerate(keep)}
def o2n(t):
    k = min(range(len(keep)), key=lambda j: abs(keep[j] / FPS - t)); return k / FPS

if '--props-out' in sys.argv:
    ch = P['chunks']; end_o = keep[-1] / FPS + 1 / FPS
    props = {'headline': dict(P['headline'], until=o2n(P['headline']['until'])),
             'chunks': [[o2n(s), o2n(ch[i + 1][0]) if i + 1 < len(ch) else len(keep) / FPS, h]
                        for i, (s, h) in enumerate(ch) if s < end_o],
             'inserts': [dict(x, start=o2n(x['start']), end=o2n(x['end'])) for x in P.get('inserts', [])],
             'durationInFrames': len(keep)}
    json.dump(props, open(sys.argv[sys.argv.index('--props-out') + 1], 'w'), ensure_ascii=False, indent=1)
    print(f"props: {len(props['chunks'])} фрагментов, {len(keep)} кадров"); sys.exit(0)
OVERLAY = LAY.endswith(('.mov', '.webm', '.mkv'))

# ---------- план кадра ----------
Z = P.get('zoom', {})
CX, CY = Z.get('center', [540, 720])
HOOK = Z.get('hook', 1.10); ALT = Z.get('alt', 1.08)
PUSH = Z.get('push', [])                                   # [[start, end, +amount], ...]
def in_push(t): return any(a <= t <= b for a, b, _ in PUSH)
bases, z = [], HOOK
for a, b in CUTS:
    if not in_push(b): z = 1.0 if z > 1.0 else ALT
    bases.append((b, z))
ease = lambda p: p * p * (3 - 2 * p)
def zoom(t):
    b = HOOK
    for c, zz in bases:
        if t >= c: b = zz
    for a, e, amt in PUSH:
        if a <= t <= e: b += amt * ease((t - a) / (e - a))
        elif e < t <= e + 1.8: b += amt * (1 - ease(max(0.0, (t - e - 1.0) / 0.8)))   # держим 1 с, возвращаем за 0,8 с
    return b

# ---------- слои ----------
WHITE_LIN = 0.58   # 0.2647 = опорный белый (75%): на HDR-экране текст выглядел серым рядом с белой футболкой (14.11.2026)
HLG_M = np.array([[0.6274, 0.3293, 0.0433], [0.0691, 0.9195, 0.0114], [0.0164, 0.0880, 0.8956]])
def srgb_to_hlg(x):
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    lin = np.clip(lin @ HLG_M.T * WHITE_LIN, 0, 1)              # белый слоя ≈ 90% сигнала HLG — на уровне светлой одежды в кадре
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    return np.where(lin <= 1 / 12, np.sqrt(3 * lin), a * np.log(np.maximum(12 * lin - b, 1e-6)) + c)
KR, KB = (0.2627, 0.0593) if HLG or MAT.startswith('bt2020') else (0.2126, 0.0722)
def layer(png):
    return layer_arr(np.asarray(Image.open(png).convert('RGBA')))
def layer_arr(arr):
    im = arr.astype(np.float32) / 255
    rgb, a = im[..., :3], im[..., 3]
    if HLG: rgb = srgb_to_hlg(rgb)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = KR * r + (1 - KR - KB) * g + KB * b
    Y = 64 + 876 * y; U = 512 + 896 * (b - y) / (2 - 2 * KB); V = 512 + 896 * (r - y) / (2 - 2 * KR)
    half = lambda x: cv2.resize(x.astype(np.float32), (x.shape[1] // 2, x.shape[0] // 2), interpolation=cv2.INTER_AREA)
    rows = np.where(a.max(1) > 0)[0]
    box = (max(0, rows[0] - 20) & ~1, min(a.shape[0] - 40, rows[-1] + 20) & ~1) if len(rows) else (0, 2)
    return dict(Y=Y.astype(np.float32), U=half(U), V=half(V), A=a.astype(np.float32), A2=half(a), box=box)
HEAD_UNTIL = o2n(P['headline']['until'])
subs = []
if not OVERLAY:
    head = layer(f'{LAY}/head.png')
    chunks = P['chunks']
    for i, (s, _) in enumerate(chunks):
        e = chunks[i + 1][0] if i + 1 < len(chunks) else NSRC / FPS
        subs.append((o2n(s), o2n(e), layer(f'{LAY}/s{i:03d}.png')))
else:
    ovdec = subprocess.Popen(['ffmpeg', '-v', 'quiet', '-i', LAY, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], stdout=subprocess.PIPE)
    def next_overlay():
        b = ovdec.stdout.read(W * H * 4)
        if len(b) < W * H * 4: return None
        a = np.frombuffer(b, np.uint8).reshape(H, W, 4)
        rows = np.where(a[..., 3].max(1) > 0)[0]
        if not len(rows): return None
        y0, y1 = max(0, rows[0] - 2) & ~1, min(H, rows[-1] + 4) & ~1
        L = layer_arr(a[y0:y1])
        L['box'] = (0, y1 - y0); L['off'] = y0
        return L

def blend(pl, L, alpha=1.0, dy=0):
    y0, y1 = L['box']; dy = (dy & ~1) + L.get('off', 0)
    A = L['A'][y0:y1] * alpha
    pl[0][y0 + dy:y1 + dy] = A * L['Y'][y0:y1] + (1 - A) * pl[0][y0 + dy:y1 + dy]
    h0, h1, d2 = y0 // 2, y1 // 2, dy // 2
    A2 = L['A2'][h0:h1] * alpha
    for k, key in ((1, 'U'), (2, 'V')):
        pl[k][h0 + d2:h1 + d2] = A2 * L[key][h0:h1] + (1 - A2) * pl[k][h0 + d2:h1 + d2]

def warp(p, z, cx, cy):
    if abs(z - 1) < 1e-4: return p
    M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
    return cv2.warpAffine(p, M, (p.shape[1], p.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

# ---------- звук: ровно по оставленным кадрам ----------
runs, r = [], [keep[0], keep[0]]
for i in keep[1:]:
    if i == r[1] + 1: r[1] = i
    else: runs.append(r); r = [i, i]
runs.append(r)
segs = [(a / FPS, (b + 1) / FPS) for a, b in runs]
af = ''.join(f"[0:a]atrim={a:.6f}:{b:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b - a - 0.008:.6f}:d=0.008[a{i}];"
             for i, (a, b) in enumerate(segs))
af += ''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1[aout]'
AUD = OUT + '.audio.m4a'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-filter_complex', af, '-map', '[aout]', '-c:a', 'aac', '-b:a', '256k', AUD], check=True)

# ---------- кадры ----------
x265p = f'colorprim={PRIM}:transfer={TRC}:colormatrix={MAT}:range=limited:log-level=error'
dec = subprocess.Popen(['ffmpeg', '-v', 'quiet', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'yuv420p10le', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p10le', '-s', f'{W}x{H}', '-r', f'{num}/{den}', '-i', '-',
    '-i', AUD, '-map', '0:v', '-map', '1:a', '-c:v', 'libx265', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p10le', '-tag:v', 'hvc1',
    '-color_primaries', PRIM, '-color_trc', TRC, '-colorspace', MAT, '-color_range', 'tv', '-x265-params', x265p,
    '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
FS = W * H * 3; ANIM = 4; n = 0; zs = []
last = keep[-1]
for i in range(NSRC):
    buf = dec.stdout.read(FS)
    if len(buf) < FS or i > last: break
    if i not in newt: continue
    t = newt[i]; a = np.frombuffer(buf, np.uint16)
    pl = [a[:W * H].reshape(H, W).astype(np.float32),
          a[W * H:W * H * 5 // 4].reshape(H // 2, W // 2).astype(np.float32),
          a[W * H * 5 // 4:].reshape(H // 2, W // 2).astype(np.float32)]
    z = zoom(i / FPS); zs.append(z)
    pl = [warp(pl[0], z, CX, CY), warp(pl[1], z, CX / 2, CY / 2), warp(pl[2], z, CX / 2, CY / 2)]
    if OVERLAY:
        L = next_overlay()
        if L is not None: blend(pl, L)
    elif t < HEAD_UNTIL + 0.3:                                   # заголовок только на хуке, уходит за 0,3 с
        blend(pl, head, alpha=1.0 if t <= HEAD_UNTIL else 1 - (t - HEAD_UNTIL) / 0.3)
    for s, e, L in subs:
        if s - 1e-6 <= t < e - 1e-6:
            p = min(1.0, (round((t - s) * FPS) + 1) / ANIM); p = 1 - (1 - p) ** 2
            blend(pl, L, alpha=p, dy=int(round(14 * (1 - p))))
            break
    enc.stdin.write(np.concatenate([np.clip(x, 0, 1023).astype(np.uint16).ravel() for x in pl]).tobytes()); n += 1
enc.stdin.close(); enc.wait(); dec.terminate()
subprocess.run(['rm', '-f', AUD])
print(f'кадров {n}, длительность {n / FPS:.2f} с (было {NSRC / FPS:.2f}), HDR: {HLG}, зум {min(zs):.2f}–{max(zs):.2f}')
