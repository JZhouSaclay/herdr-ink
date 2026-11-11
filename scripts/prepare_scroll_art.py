"""Split the actual GPT Image 2 scroll into fixed-size caps and repeatable edges."""
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'mods/ink-chrome/art';src=Image.open(R/'candidates/gpt-image-2-scroll/generated-1.png').convert('RGBA')
# Fixed caps keep their proportions; centre spans and sides repeat in clipped
# containers, so arbitrary panel widths/heights do not stretch the painting.
for end,y in [('top',56),('bottom',1435)]:
 for part,x,w in [('left',142,70),('mid',212,600),('right',812,70)]:
  im=src.crop((x,y,x+w,y+60));im.resize((round(w*.4),24),Image.Resampling.LANCZOS).save(D/f'scroll-{end}-{part}-v25.png')
for side,x in [('left',162),('right',820)]:
 im=src.crop((x,220,x+32,604)).resize((8,96),Image.Resampling.LANCZOS);im.save(D/f'scroll-{side}-v25.png')
# Feather repeat boundaries to avoid seams in long axes.
for end in ['top','bottom']:
 p=D/f'scroll-{end}-mid-v25.png';a=np.array(Image.open(p).convert('RGBA'),dtype=float)
 mid=(a[:,0,:]+a[:,-1,:])/2
 for i in range(20):
  f=(20-i)/20
  a[:,i,:]=a[:,i,:]*(1-f)+mid*f
  a[:,-1-i,:]=a[:,-1-i,:]*(1-f)+mid*f
 Image.fromarray(a.clip(0,255).astype('uint8')).save(p)
# Original transparent art on the app's paper color, for reviewing provenance.
bg=Image.new('RGBA',src.size,'#f8f9f5');bg.alpha_composite(src);bg.convert('RGB').save(R/'candidates/gpt-image-2-scroll/on-paper.png')
print('Prepared 8 original-art slices; caps stay fixed and sides tile responsively')
