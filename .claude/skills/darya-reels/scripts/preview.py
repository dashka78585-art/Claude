"""Кадр-превью из ГОТОВОГО видео в цветах, как его показывает айфон Дарьи (только для согласования; видео не меняется).
Калибровка: preview_lut_lab.npy — кривые в Lab, подогнанные по её скриншоту ролика с телефона (14.11.2026).
Использование: python3 preview.py <video> <секунда> <out.jpg|png> [ширина=540]
"""
import subprocess, sys, os
import numpy as np, cv2
v, t, out = sys.argv[1:4]; wd = int(sys.argv[4]) if len(sys.argv) > 4 else 540
raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', t, '-i', v, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                      '-vf', 'scale=1080:1920', '-'], capture_output=True, check=True).stdout
rgb = np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3)
trc = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=color_transfer', '-of', 'csv=p=0', v],
                     capture_output=True, text=True).stdout.strip()
if trc == 'arib-std-b67':                       # HDR: применяем калибровку под экран айфона
    lut = np.load(os.path.join(os.path.dirname(__file__), 'preview_lut_lab.npy'))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    lab = np.stack([lut[c][lab[..., c]] for c in range(3)], -1).astype(np.uint8)
    rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
h = round(1920 * wd / 1080)
cv2.imwrite(out, cv2.cvtColor(cv2.resize(rgb, (wd, h), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
