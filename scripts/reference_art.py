"""Use the supplied real ink marks instead of geometric approximations.
Bamboo material uses Titus Tscharntke's public-domain photo (see ART-NOTICE.md).
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'mods/ink-chrome/art'
reference=Image.open(ROOT/'reference/ink-reference.png').convert('RGB')

def ink_crop(box, target, color=(49,65,60), flip=False):
    crop=reference.crop(box)
    if flip:crop=ImageOps.mirror(crop)
    a=np.asarray(crop,dtype=float).mean(2)
    # The scan's paper is about 245. Preserve real feathering, not the paper.
    alpha=np.clip((241-a)/232,0,1)
    alpha[alpha<.018]=0
    rgba=np.zeros((*alpha.shape,4),dtype='uint8')
    rgba[:,:,:3]=color;rgba[:,:,3]=np.round(alpha*255).astype('uint8')
    result=Image.fromarray(rgba)
    if target.startswith('stroke'):
        # Herdr's image element contains its intrinsic aspect ratio. Give the
        # brush a wide intrinsic canvas so it spans the whole navigation row.
        result=result.resize((1200,200),Image.Resampling.LANCZOS)
    result.save(ART/target)

ink_crop((23,489,344,649),'stroke-v3.png')
ink_crop((383,151,697,231),'stroke-alt-v3.png',flip=True)
ink_crop((399,761,676,1046),'ink-ring-v3.png',color=(73,107,101))
(ART/'check-v2.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path fill="#000" d="M3 10.2 5.3 9.4 8.3 12.1 16.8 4.8 17.1 6.2 8.1 15.5Z"/></svg>\n')

# Use an actual split bamboo surface and its real braided bindings.
photo=Image.open(ROOT/'reference/bamboo-table.jpg').convert('RGB')
slat=photo.crop((805,180,833,1030)).rotate(90,expand=True)
# Separate the bindings from the writing surface so they stay near the ends.
# In the rotated photo the first binding is near x=130 and the other at x=700.
w,h=1200,220
left=slat.crop((80,0,180,slat.height)).resize((105,176),Image.Resampling.LANCZOS)
center=slat.crop((245,0,620,slat.height)).resize((970,176),Image.Resampling.LANCZOS)
right=slat.crop((670,0,770,slat.height)).resize((105,176),Image.Resampling.LANCZOS)
material=Image.new('RGB',(1180,176));material.paste(left,(0,0));material.paste(center,(105,0));material.paste(right,(1075,0))
a=np.asarray(material,dtype=float)
# Lift the photographic surface to pale natural bamboo, retaining its grain and cords.
luma=a@np.array([.2126,.7152,.0722])
shade=(luma-np.median(luma))*.70
rgb=np.clip(np.array([237,239,233])+shade[:,:,None],0,255).astype('uint8')
mat=Image.fromarray(rgb).convert('RGBA')
mask=Image.new('L',mat.size);d=ImageDraw.Draw(mask)
# Slightly irregular cut ends and restrained edge bevel, no paper-ticket outline.
d.polygon([(5,9),(16,3),(1157,5),(1175,11),(1179,158),(1165,173),(15,175),(0,164)],fill=255)
mat.putalpha(mask.filter(ImageFilter.GaussianBlur(.45)))
slip=Image.new('RGBA',(w,h))
# Low relief from the cut bamboo edge, kept small enough for a compact tab.
shadow=Image.new('RGBA',(w,h));shadow.paste((55,67,47,45),(12,29,1192,205))
shadow.putalpha(Image.new('L',(w,h)))
sm=Image.new('L',(w,h));sm.paste(mask,(12,27));sm=sm.filter(ImageFilter.GaussianBlur(3));sm=sm.point(lambda x:int(x*.12));shadow.putalpha(sm)
slip=Image.alpha_composite(slip,shadow)
slip.alpha_composite(mat,(10,20))
d=ImageDraw.Draw(slip)
d.line([(27,25),(1167,27)],fill=(255,253,238,175),width=2)
d.line([(27,193),(1175,191)],fill=(126,113,77,90),width=2)
slip.save(ART/'bamboo-v4.png')
# Small standalone animation preview uses precisely the same extracted ring as Herdr.
ring=Image.open(ART/'ink-ring-v3.png').resize((104,104),Image.Resampling.LANCZOS)
frames=[]
for i in range(40):
    frame=Image.new('RGBA',(144,144),(252,252,249,255))
    frame.alpha_composite(ring.rotate(-i*9,resample=Image.Resampling.BICUBIC,expand=False),(20,20))
    frames.append(frame.convert('RGB'))
frames[0].save(ROOT/'ink-ring-preview.gif',save_all=True,append_images=frames[1:],duration=40,loop=0)
print('Real ink and bamboo assets:',ART)

# A light, uneven four-sided border assembled from actual brush texture.
frame=Image.new('RGBA',(1200,200))
edge=Image.open(ART/'stroke-alt-v3.png')
horizontal=edge.resize((1168,12),Image.Resampling.LANCZOS)
frame.alpha_composite(horizontal,(16,0))
frame.alpha_composite(ImageOps.flip(ImageOps.mirror(horizontal)),(16,188))
vertical=edge.rotate(90,expand=True).resize((10,176),Image.Resampling.LANCZOS)
frame.alpha_composite(vertical,(2,12))
frame.alpha_composite(ImageOps.flip(vertical),(1188,12))
frame.save(ART/'row-frame-v4.png')
