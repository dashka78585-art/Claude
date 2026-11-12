# sRGB(bt709) PNG -> HLG(bt2020) code values, SDR white mapped to HLG reference white (~75%)
import numpy as np,sys,glob
from PIL import Image
M=np.array([[0.6274,0.3293,0.0433],[0.0691,0.9195,0.0114],[0.0164,0.0880,0.8956]])
a,b,c=0.17883277,0.28466892,0.55991073
def conv(x):
    x=x/255.0
    lin=np.where(x<=0.04045,x/12.92,((x+0.055)/1.055)**2.4)
    lin=lin@M.T*0.2647
    lin=np.clip(lin,0,1)
    return np.where(lin<=1/12,np.sqrt(3*lin),a*np.log(np.maximum(12*lin-b,1e-6))+c)
for f in sys.argv[1:]:
    im=np.asarray(Image.open(f).convert('RGBA')).astype(np.float64)
    rgb=conv(im[...,:3])
    out=np.dstack([np.round(rgb*255),im[...,3]]).astype(np.uint8)
    Image.fromarray(out,'RGBA').save(f)
