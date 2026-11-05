"""Ink crane animation derived from the user's painting reference.
Actual painted body/feathers are masked into layers, not redrawn as vector icons.
Only key poses 01–06 are played slowly; the final pose remains in flight.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'mods/ink-chrome/art'
REF=Image.open(ROOT/'reference/crane-ink-reference.png').convert('RGB')
REST=REF.crop((65,606,355,1145))
FLIGHT=REF.crop((430,600,810,1088))
SIZE=(640,620);PIVOT=(320,305)

def extract(im,polygon,body=False):
    rgb=np.asarray(im,dtype=float)
    # Neutralize scanned paper while preserving the original ink wash and dry edges.
    bg=np.array([238,236,231]) if body else np.array([255,255,255])
    rgb=np.clip(rgb/bg*np.array([249,251,249]),0,255).astype('uint8')
    mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.polygon(polygon,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(.65))
    alpha=np.asarray(mask,dtype=float)
    if not body:
        # Feather layer white paper becomes transparent; ink and grey washes stay.
        lum=np.asarray(im,dtype=float).mean(2)
        alpha*=np.clip((254-lum)/120,0,1)
    else:
        # Remove blossoms from the backdrop, retaining only the red crown on the head.
        original=np.asarray(im,dtype=float);yy=np.arange(im.height)[:,None]
        red=(original[:,:,0]>original[:,:,1]*1.25)&(original[:,:,0]>original[:,:,2]*1.25)&(yy>65)
        alpha[red]=0
    rgba=np.concatenate([rgb,np.clip(alpha,0,255).astype('uint8')[:,:,None]],axis=2)
    return Image.fromarray(rgba)

body_outline=[(9,18),(57,31),(80,34),(88,29),(104,31),(115,43),(113,59),(119,78),(123,105),(120,135),(123,159),(132,180),(156,195),(181,214),(207,240),(219,255),(245,260),(272,277),(286,296),(286,326),(280,343),(287,362),(280,375),(274,355),(274,388),(262,371),(266,407),(258,395),(251,415),(247,393),(233,398),(225,382),(211,393),(206,380),(192,378),(180,363),(174,341),(161,332),(148,331),(134,321),(119,303),(107,284),(95,262),(88,240),(86,218),(89,198),(92,179),(94,156),(95,132),(96,109),(96,86),(90,64),(81,53),(63,43),(9,21)]
# Only the nearly vertical supporting leg and its foot are retained.
leg_outline=[(143,324),(155,324),(162,393),(157,449),(154,496),(165,510),(177,526),(172,532),(147,518),(102,512),(101,501),(141,500),(144,446),(146,403)]
core=extract(REST,body_outline,body=True)
leg=extract(REST,leg_outline,body=True)
wing_outline=[(129,214),(141,153),(155,114),(174,82),(219,55),(273,34),(325,14),(379,0),(376,40),(351,52),(328,74),(303,112),(267,143),(237,166),(208,194),(176,220),(152,225)]
wing=extract(FLIGHT,wing_outline)
core.save(ART/'crane-ink-body-v7.png');leg.save(ART/'crane-ink-single-leg-v7.png');wing.save(ART/'crane-ink-wing-v7.png')

body_field=Image.new('RGBA',SIZE);body_field.alpha_composite(core,(170,35))
leg_field=Image.new('RGBA',SIZE);leg_field.alpha_composite(leg,(170,35))
wing_field=Image.new('RGBA',SIZE);wing_field.alpha_composite(wing,(165,90))

def fade(im,opacity):
    im=im.copy();im.putalpha(im.getchannel('A').point(lambda x:int(x*opacity)));return im

def wing_pose(angle,scale=1,opacity=1):
    im=wing_field.rotate(angle,resample=Image.Resampling.BICUBIC,center=PIVOT)
    if scale!=1:
        # Transform around the shoulder, so folding stays attached to the body.
        a=1/scale;px,py=PIVOT
        im=im.transform(SIZE,Image.Transform.AFFINE,(a,0,px-px*a,0,a,py-py*a),resample=Image.Resampling.BICUBIC)
    return fade(im,opacity)

# Only the requested original poses 01–06. Smooth interpolation preserves
# the same six silhouettes, removing every fold/landing/leg-extension pose.
KEY_ANGLES=(0,-44,-94,-44,0,-48)
KEY_INTERVAL_MS=400
STEP_MS=40
DURATION_MS=2000
angles=[]
for a,b in zip(KEY_ANGLES,KEY_ANGLES[1:]):
    for step in range(KEY_INTERVAL_MS//STEP_MS):
        u=step/(KEY_INTERVAL_MS//STEP_MS)
        eased=(1-math.cos(math.pi*u))/2
        angles.append(a+(b-a)*eased)
angles.append(KEY_ANGLES[-1])

def flight_pose(angle):
    canvas=Image.new('RGBA',SIZE)
    near=wing_pose(angle)
    canvas.alpha_composite(fade(near.transpose(Image.Transpose.FLIP_LEFT_RIGHT),.50))
    canvas.alpha_composite(leg_field.rotate(57,resample=Image.Resampling.BICUBIC,center=(320,365)))
    canvas.alpha_composite(body_field)
    canvas.alpha_composite(near)
    return canvas.rotate(18,resample=Image.Resampling.BICUBIC,center=PIVOT)

poses=[flight_pose(a) for a in angles]
# Decode a small native ornament, rather than fifty full reference-sized frames.
OUTPUT=(320,310)
small=[im.resize(OUTPUT,Image.Resampling.LANCZOS) for im in poses]
small[-1].save(ART/'crane-rest-ink-left-v8.png')
palette_frames=[]
for im in small:
    matte=Image.new('RGBA',OUTPUT,(248,250,248,255));matte.alpha_composite(im)
    q=matte.convert('RGB').quantize(colors=255)
    data=np.array(q);data[np.asarray(im.getchannel('A'))<20]=255
    out=Image.frombytes('P',OUTPUT,data.tobytes());out.putpalette(q.getpalette()[:765]+[248,250,248]);out.info['transparency']=255
    palette_frames.append(out)
# Final hold guards against decoder looping before the one-time PNG handoff.
palette_frames[0].save(ART/'crane-arrival-ink-left-v8.gif',save_all=True,append_images=palette_frames[1:],duration=[STEP_MS]*(len(small)-1)+[1000],transparency=255,disposal=2,optimize=False)

font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',17)
sheet=Image.new('RGB',(1200,300),(248,250,248));d=ImageDraw.Draw(sheet)
for i,angle in enumerate(KEY_ANGLES):
    thumb=flight_pose(angle).resize((198,192),Image.Resampling.LANCZOS)
    sheet.paste(thumb,(i*200+1,15),thumb)
    d.text((i*200+22,245),f'{i+1:02d} · {i*400}ms',font=font,fill=(65,79,70))
sheet.save(ROOT/'crane-poses-v8.png')

frames=[]
for ms in range(0,3200,STEP_MS):
    base=Image.new('RGBA',(800,250),(248,250,248,255));d=ImageDraw.Draw(base)
    d.text((26,20),'慢速飞入 · 仅 01–06 · 保留飞行姿态',font=font,fill=(96,107,100))
    border=Image.open(ART/'row-frame-v4.png').resize((740,150),Image.Resampling.LANCZOS);border.putalpha(border.getchannel('A').point(lambda a:int(a*.66)));base.alpha_composite(border,(24,68))
    d=ImageDraw.Draw(base);d.text((49,132),'水墨书斋',font=ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc',26),fill=(48,54,50))
    t=min(ms/1600,1);ease=1-(1-t)**3;opacity=(1-(1-min(ms/400,1))**3)*.88
    bird=fade(poses[min(ms//STEP_MS,len(poses)-1)].resize((126,122),Image.Resampling.LANCZOS),opacity)
    slot=Image.new('RGBA',(142,135));slot.alpha_composite(bird,(round(49*(1-ease)),round(-17.5*(1-ease))))
    base.alpha_composite(slot,(612,74));frames.append(base.convert('RGB'))
frames[0].save(ROOT/'crane-arrival-preview-v8.gif',save_all=True,append_images=frames[1:],duration=STEP_MS,loop=0)
print('Generated poses 01–06 only: 2s flight, smooth 25fps, no folding or landing')
