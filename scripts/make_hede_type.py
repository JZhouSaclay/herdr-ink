"""Render the Hede brush wordmark and make a 1.6% wider terminal font.
The interface retains the original WenKai face. Only terminal advances change.
"""
from pathlib import Path
from collections import Counter
import json,hashlib
import numpy as np
from PIL import Image,ImageFont,ImageDraw
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parents[1];F=R/'mods/ink-chrome/fonts';A=R/'mods/ink-chrome/art'
source=F/'LXGWWenKaiMono-Regular.ttf';out=F/'HedeInkMono-Regular.ttf'
f=TTFont(source)
before=Counter(advance for advance,_ in f['hmtx'].metrics.values())
for name,(advance,bearing) in list(f['hmtx'].metrics.items()):
    f['hmtx'].metrics[name]=(round(advance*1.016),bearing)
f['hhea'].advanceWidthMax=max(a for a,_ in f['hmtx'].metrics.values())
f['OS/2'].recalcAvgCharWidth(f)
# The original OFL reserves LXGW and related Chinese names; use a new family.
labels={1:'Hede Ink Mono',2:'Regular',3:'Hede Ink Mono Regular 1.530 spacing 1.016',4:'Hede Ink Mono Regular',6:'HedeInkMono-Regular',16:'Hede Ink Mono',17:'Regular',18:'Hede Ink Mono Regular',21:'Hede Ink Mono',22:'Regular'}
for record in list(f['name'].names):
    if record.nameID in labels:f['name'].setName(labels[record.nameID],record.nameID,record.platformID,record.platEncID,record.langID)
f['name'].setName('Derived from LXGW WenKai Mono v1.530; horizontal advances increased 1.6%; outlines unchanged.',10,3,1,0x409)
if 'DSIG' in f:del f['DSIG']
f.save(out)
check=TTFont(out);c=check.getBestCmap();widths={ch:check['hmtx'][c[ord(ch)]][0] for ch in 'iM0 宋楷'}
assert len({widths[ch] for ch in 'iM0 '})==1 and widths['宋']==2*widths['i']
assert check['head'].unitsPerEm==f['head'].unitsPerEm and check['post'].isFixedPitch
assert TTFont(source).getTableData('glyf')==check.getTableData('glyf'),'glyph outlines must remain byte-identical'

# Zhi Mang Xing's actual brush outlines, rasterized to a transparent, font-free mark.
brandface=R/'reference/Zhi-Mang-Xing-brand.ttf'
font=ImageFont.truetype(str(brandface),300)
im=Image.new('RGBA',(900,460));d=ImageDraw.Draw(im);d.text((28,12),'何德',font=font,fill=(31,43,35,255))
im=im.crop(im.getbbox());alpha=np.asarray(im.getchannel('A'),dtype=float)
y,x=np.indices(alpha.shape);rng=np.random.default_rng(13)
# Small, fixed dry-brush fibres: preserve thick turns and legibility at 36px.
wash=np.clip(.97+.025*np.sin(x*.33+y*.075)+.02*np.sin(x*1.3-y*.2),.88,1)
dry=(np.sin(x*.79+y*.21)>.94)&(rng.random(alpha.shape)>.78)
alpha*=wash;alpha[dry]*=.38
im.putalpha(Image.fromarray(np.clip(alpha,0,255).astype('uint8')))
canvas=Image.new('RGBA',(im.width+32,im.height+22));canvas.alpha_composite(im,(16,11))
canvas.save(A/'hede-calligraphy-v13.png')
preview=Image.new('RGBA',canvas.size,(248,250,248,255));preview.alpha_composite(canvas);preview.convert('RGB').save(R/'hede-calligraphy-preview-v13.png')
(R/'font-spacing-v13.json').write_text(json.dumps({'ui_family':'LXGW WenKai Mono','terminal_family':'Hede Ink Mono','original_font':'LXGW WenKai Mono v1.530','advance_ratio':1.016,'font_size':14,'extra_advance_px':{'latin':.112,'cjk':.224},'outlines_byte_identical':True,'widths':widths,'font_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'wordmark':{'text':'何德','face':'Zhi Mang Xing','source':'https://github.com/google/fonts/tree/main/ofl/zhimangxing','license':'SIL OFL 1.1','format':'transparent PNG'}},ensure_ascii=False,indent=2)+'\n')
print('Wordmark generated; terminal spacing +1.6%; outlines byte-identical:',widths)
