"""Retain photographed bamboo and scanned ink; fit actual native element bounds."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'mods/ink-chrome/art'
# Match fixed tab widths, so native contain sizing cannot flatten a short label.
source=Image.open(ART/'bamboo-v4.png').convert('RGBA')
for width in range(112,225,8):source.resize((width*3,120),Image.Resampling.LANCZOS).save(ART/f'bamboo-v9-{width}.png')

def runs(row,threshold):
    on=np.r_[False,row>=threshold,False];edges=np.flatnonzero(on[1:]!=on[:-1]);return zip(edges[::2],edges[1::2])

def svg_mask(im,path):
    a=np.asarray(im.getchannel('A'));h,w=a.shape
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">']
    # Four cumulative layers approximate original alpha, keeping gaps and grain.
    for threshold in [32,96,160,224]:
        parts.append('<g fill="#000" opacity="0.25">')
        for y,row in enumerate(a):
            for x0,x1 in runs(row,threshold):parts.append(f'<path d="M{x0} {y}h{x1-x0}v1H{x0}Z"/>')
        parts.append('</g>')
    parts.append('</svg>');path.write_text(''.join(parts)+'\n')
svg_mask(Image.open(ART/'ink-ring-v3.png').convert('RGBA'),ART/'ink-ring-v9.svg')
# Square seal from real brush texture. Normalize each side before assembly.
stroke=Image.open(ART/'stroke-alt-v3.png').convert('RGBA')
seal=Image.new('RGBA',(68,68));h=stroke.resize((60,5),Image.Resampling.LANCZOS)
seal.alpha_composite(h,(4,1));seal.alpha_composite(h.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(4,62))
v=stroke.rotate(90,expand=True).resize((5,56),Image.Resampling.LANCZOS)
seal.alpha_composite(v,(1,6));seal.alpha_composite(v.transpose(Image.Transpose.FLIP_TOP_BOTTOM),(62,6))
svg_mask(seal,ART/'ink-seal-v9.svg')
# Record real scan coverage as runs. Native percent-x/pixel-y paths can stretch
# across any width without stretching the 4px stroke thickness or polling size.
a=np.asarray(stroke.resize((384,7),Image.Resampling.LANCZOS).getchannel('A'))
bands=[]
for threshold in [40,120,200]:
    bands.append([[int(x0),int(x1),y] for y,row in enumerate(a) for x0,x1 in runs(row,threshold)])
(ROOT/'scripts/ink-coverage.json').write_text(json.dumps(bands,separators=(',',':'))+'\n')
print('Generated 11 bamboo proportions, native spinner SVG, brush seal, and scanned line coverage')
