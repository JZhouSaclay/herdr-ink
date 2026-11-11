"""Transparent dark-ink bamboo leaf, occupying the same slot as tab numbers."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];S=24
def curve(a,b,c,d):
 return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1)) for t in np.linspace(0,1,160)]
im=Image.new('RGBA',(20*S,18*S));mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
outline=curve((5,14),(4.5,8),(11.5,1.3),(18.3,.9))+curve((18.3,.9),(18.0,8.8),(12.2,14.8),(5,14))
d.polygon([(x*S,y*S) for x,y in outline],fill=248)
stem=curve((2.2,16.9),(6.7,12.7),(12.4,6.6),(18.2,1.1));d.line([(x*S,y*S) for x,y in stem],fill=246,width=round(.65*S))
a=np.asarray(mask.filter(ImageFilter.GaussianBlur(.025*S)),dtype=float);yy,xx=np.indices(a.shape)
rng=np.random.default_rng(35);texture=.95+.04*np.sin(xx*.14+yy*.11)+.02*np.sin(xx*.65-yy*.29)
a*=np.clip(texture,.85,1);a[(rng.random(a.shape)>.994)&(a>100)]*=.45
rgba=np.zeros((*a.shape,4),dtype='uint8');rgba[:,:,:3]=[35,58,43];rgba[:,:,3]=np.clip(a,0,255).astype('uint8');im=Image.fromarray(rgba)
# A restrained vein makes the leaf readable without bright color or extra badges.
d=ImageDraw.Draw(im);vein=curve((6.2,12.5),(9.1,10),(13.4,5.5),(16.6,2.9));d.line([(x*S,y*S) for x,y in vein],fill=(204,214,200,95),width=round(.15*S))
im.save(R/'mods/ink-chrome/art/tab-leaf-v19.png')
