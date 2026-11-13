# Auto-edit: cut pauses, punch-in zooms, animated subtitles. HDR (HLG, 10-bit) preserved.
import json, subprocess, sys, numpy as np, cv2
from PIL import Image

SRC = 'in/gv.mov'; OUT = sys.argv[1]
FPS = 30; W, H = 1080, 1920; NSRC = 2274
CX, CY = 540, 720                      # zoom centre (face)

# ---------- cuts (original seconds) ----------
CUTS = [(1.82,2.36),(6.16,6.60),(13.52,14.09),(17.05,17.37),(18.23,18.64),(23.77,24.47),
        (52.79,53.28),(55.35,55.67),(56.22,56.53),(61.92,62.53),(70.14,70.50)]
CUTS = [(a+0.06, b-0.08) for a, b in CUTS]
def kept(t): return not any(a <= t < b for a, b in CUTS)
keep = [i for i in range(NSRC) if kept(i/FPS)]
newt = {i: k/FPS for k, i in enumerate(keep)}           # src frame -> new time
def o2n(t):                                              # orig time -> new time
    i = min(range(len(keep)), key=lambda k: abs(keep[k]/FPS - t)); return i/FPS

# ---------- zoom plan (orig seconds) ----------
PUSH = [(37.46, 39.10, .10), (56.86, 58.98, .10), (67.70, 75.81, .12)]
cut_points = [b for a, b in CUTS]
def in_push(t): return any(a <= t <= b for a, b, _ in PUSH)
# base zoom: hook starts close, then alternates at each cut (not inside push windows)
bases = []; z = 1.10
for c in cut_points:
    if not in_push(c): z = 1.0 if z > 1.0 else 1.08
    bases.append((c, z))
def zoom(t):
    b = 1.10
    for c, zz in bases:
        if t >= c: b = zz
    ease = lambda p: p*p*(3 - 2*p)
    for a, e, amt in PUSH:
        if a <= t <= e:
            b += amt * ease((t - a) / (e - a))
        elif e < t <= e + 1.8:                       # hold 1 s, then ease back in 0.8 s
            b += amt * (1 - ease(max(0.0, (t - e - 1.0) / 0.8)))
    return b

# ---------- overlays (already HLG-coded RGBA PNGs) ----------
def to_yuv(png):
    im = np.asarray(Image.open(png).convert('RGBA')).astype(np.float32) / 255
    r, g, b, a = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    y = 0.2627*r + 0.6780*g + 0.0593*b
    cb = (b - y) / 1.8814; cr = (r - y) / 1.4746
    Y = 64 + 876*y; U = 512 + 896*cb; V = 512 + 896*cr
    half = lambda x: cv2.resize(x, (W//2, H//2), interpolation=cv2.INTER_AREA)
    ys, ye = np.where(a.max(1) > 0)[0][[0, -1]] if a.max() > 0 else (0, 0)
    return dict(Y=Y, U=half(U), V=half(V), A=a, A2=half(a), box=(max(0, ys-20), min(H, ye+40)))
head = to_yuv('r3/head.png')
C = json.load(open('chunks2.json'))
subs = [(o2n(s), o2n(e), to_yuv(f'r3/s{i:03d}.png')) for i, (s, e, _) in enumerate(C)]

def blend(planes, ov, alpha=1.0, dy=0):
    Yp, Up, Vp = planes
    y0, y1 = ov['box']
    A = ov['A'][y0:y1] * alpha
    Ys = ov['Y'][y0:y1]
    t0, t1 = y0 + dy, y1 + dy
    Yp[t0:t1] = A*Ys + (1-A)*Yp[t0:t1]
    h0, h1 = y0//2, y1//2; A2 = ov['A2'][h0:h1] * alpha
    Up[h0+dy//2:h1+dy//2] = A2*ov['U'][h0:h1] + (1-A2)*Up[h0+dy//2:h1+dy//2]
    Vp[h0+dy//2:h1+dy//2] = A2*ov['V'][h0:h1] + (1-A2)*Vp[h0+dy//2:h1+dy//2]

def warp(p, z, cx, cy):
    if abs(z - 1) < 1e-4: return p
    M = np.float32([[z, 0, cx*(1-z)], [0, z, cy*(1-z)]])
    return cv2.warpAffine(p, M, (p.shape[1], p.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

# ---------- audio: same cuts, 8 ms fades at joins ----------
segs = []; run = [keep[0], keep[0]]
for i in keep[1:]:
    if i == run[1] + 1: run[1] = i
    else: segs.append((run[0]/FPS, (run[1]+1)/FPS)); run = [i, i]
segs.append((run[0]/FPS, (run[1]+1)/FPS))
af = ''.join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b-a-0.008}:d=0.008[a{i}];" for i, (a, b) in enumerate(segs))
af += ''.join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[aout]"
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-filter_complex', af, '-map', '[aout]', '-c:a', 'aac', '-b:a', '256k', 'cut_audio.m4a'], check=True)

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'yuv420p10le', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p10le', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
    '-i', 'cut_audio.m4a', '-map', '0:v', '-map', '1:a', '-c:v', 'libx265', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p10le', '-tag:v', 'hvc1',
    '-color_primaries', 'bt2020', '-color_trc', 'arib-std-b67', '-colorspace', 'bt2020nc', '-color_range', 'tv',
    '-x265-params', 'colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited:log-level=error',
    '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)

FS = W*H*3  # bytes per frame (10-bit 4:2:0 -> 1.5 samples * 2 bytes)
ANIM = 4
zlog = []
for i in range(NSRC):
    buf = dec.stdout.read(FS)
    if len(buf) < FS: break
    if i not in newt: continue
    t_o = i / FPS; t = newt[i]
    a = np.frombuffer(buf, np.uint16)
    Yp = a[:W*H].reshape(H, W).astype(np.float32)
    Up = a[W*H:W*H*5//4].reshape(H//2, W//2).astype(np.float32)
    Vp = a[W*H*5//4:].reshape(H//2, W//2).astype(np.float32)
    z = zoom(t_o); zlog.append(z)
    Yp = warp(Yp, z, CX, CY); Up = warp(Up, z, CX/2, CY/2); Vp = warp(Vp, z, CX/2, CY/2)
    planes = [Yp, Up, Vp]
    blend(planes, head)
    for s, e, ov in subs:
        if s - 1e-6 <= t < e - 1e-6:
            k = int(round((t - s) * FPS))
            p = min(1.0, (k + 1) / ANIM); p = 1 - (1-p)**2
            blend(planes, ov, alpha=p, dy=int(round(14*(1-p))) & ~1)
            break
    out = np.concatenate([np.clip(x, 0, 1023).astype(np.uint16).ravel() for x in planes])
    enc.stdin.write(out.tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print('frames out', len(zlog), 'duration %.2fs' % (len(zlog)/FPS), 'zoom range %.2f-%.2f' % (min(zlog), max(zlog)))
