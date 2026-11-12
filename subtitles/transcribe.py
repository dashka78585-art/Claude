import json,sys
from faster_whisper import WhisperModel
m=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=4)
prompt="Грудное вскармливание, ГВ, докорм, смесь, педиатр, свекровь."
from faster_whisper.audio import decode_audio
import numpy as np,wave
wf=wave.open(sys.argv[1]);a=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
segs,info=m.transcribe(a,language='ru',word_timestamps=True,initial_prompt=prompt,vad_filter=True)
out=[]
for s in segs:
    out.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'w':w.word,'s':w.start,'e':w.end} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}",flush=True)
json.dump(out,open('words.json','w'),ensure_ascii=False,indent=1)
