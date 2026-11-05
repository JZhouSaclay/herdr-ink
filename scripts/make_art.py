"""Original procedural ink-wash assets. Requires Python, Pillow, numpy; seed is fixed."""
from pathlib import Path
import random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'mods/ink-chrome/art'
ART.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(2718)
random.seed(2718)
W, H = 2400, 1600
PAPER = np.array([252., 252., 249.])
# Fibres, rather than a repeating tiled texture.
fine = rng.normal(0, .33, (H, W))
coarse = Image.fromarray(rng.integers(110, 145, (100, 150), dtype=np.uint8)).resize((W, H), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(4))
noise = fine + (np.asarray(coarse, dtype=float)-128)*.045
base = np.clip(PAPER + noise[:,:,None], 0, 255).astype('uint8')
canvas = Image.fromarray(base).convert('RGBA')
Image.fromarray(base).save(ART/'paper-v1.png')

def wash(points, alpha, blur=2, color=(85,99,94)):
    global canvas
    layer = Image.new('L', (W,H))
    # Break the polygon silhouette into irregular, brush-like ridges.
    # Never interpolate the closing bottom edge into the mountain skyline.
    bottom = len(points)
    for k,(x,y) in enumerate(points):
        if y >= H: bottom=k;break
    ridge=points[:bottom]
    irregular=[]
    for k in range(len(ridge)-1):
        x0,y0=ridge[k];x1,y1=ridge[k+1]
        steps=max(2,int(abs(x1-x0)/4))
        for j in range(steps):
            t=j/steps
            irregular.append((x0+(x1-x0)*t,y0+(y1-y0)*t+random.uniform(-3.8,3.8)))
    irregular.append(ridge[-1])
    ImageDraw.Draw(layer).polygon(irregular+points[bottom:], fill=255)
    if blur: layer = layer.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(layer, dtype=float)/255
    # Granulated ink, fading into empty paper toward the bottom of each wash.
    yy = np.arange(H)[:,None]
    top = min(y for x,y in points)
    fade = np.clip(1-(yy-top)/(H-top+1), 0, 1)**.75
    grain = rng.uniform(.62, 1, (H,W))
    pool=Image.fromarray(rng.integers(65,255,(H//22,W//22),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    grain *= .55 + np.asarray(pool,dtype=float)/420
    xx=np.arange(W)[None,:]
    feather=np.clip((xx-min(x for x,y in ridge))/180,0,1)
    a = (a * fade * grain * feather * alpha).astype('uint8')
    ink = Image.new('RGBA',(W,H),color+(0,))
    ink.putalpha(Image.fromarray(a))
    canvas = Image.alpha_composite(canvas, ink)

# The left 45% is mostly untouched paper; ridges collect toward the lower right.
for pts, alpha, blur in [
    ([(1070,1170),(1180,1110),(1290,1100),(1380,1005),(1435,1034),(1540,888),(1580,930),(1680,823),(1730,895),(1825,951),(1920,881),(2050,1000),(2170,917),(2300,1040),(2400,986),(2400,1600),(1070,1600)],45,5),
    ([(1310,1390),(1440,1270),(1510,1250),(1595,1145),(1650,1185),(1740,1020),(1775,1060),(1840,987),(1880,1068),(1965,1130),(2045,1073),(2160,1190),(2260,1110),(2400,1200),(2400,1600),(1310,1600)],72,3),
    ([(1660,1570),(1770,1468),(1840,1395),(1930,1370),(2030,1230),(2065,1254),(2140,1168),(2200,1300),(2290,1345),(2400,1280),(2400,1600)],110,1.7),
]:
    wash(pts,alpha,blur)
# Dry-brush mountain creases, washed back into the paper.
layer = Image.new('RGBA',(W,H))
d=ImageDraw.Draw(layer)
for i in range(190):
    x=random.uniform(1510,2390); y=random.uniform(1120,1590)
    if x < 1750 and y < 1240: continue
    length=random.uniform(15,100)
    points=[(x,y),(x-random.uniform(4,16),y+length*.4),(x-random.uniform(10,32),y+length)]
    d.line(points,fill=(69,84,77,random.randint(3,15)),width=random.randint(1,3))
canvas=Image.alpha_composite(canvas,layer.filter(ImageFilter.GaussianBlur(.5)))
# Mist bands soften the foot of the mountains without hard horizontal edges.
for cy, strength, spread in [(1210,.39,49),(1440,.32,60)]:
    yy,xx=np.mgrid[0:H,0:W]
    a=(np.exp(-((yy-cy)/spread)**2)*np.clip((xx-1000)/1100,0,1)*255*strength).astype('uint8')
    mist=Image.fromarray(base).convert('RGBA'); mist.putalpha(Image.fromarray(a))
    canvas=Image.alpha_composite(canvas,mist)
# A bank of near rocks: layered, uneven faces rather than vector triangles.
wash([(1930,1599),(1975,1547),(2050,1528),(2100,1483),(2180,1495),(2208,1533),(2270,1550),(2320,1599)],112,1)
wash([(2100,1599),(2140,1560),(2230,1530),(2280,1555),(2340,1545),(2400,1580),(2400,1600)],95,1)
# Sparse bamboo in the far right margin, tapered strokes and small leaf clusters.
layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
for bx,by,height,lean in [(2120,1580,450,-65),(2185,1590,370,-20),(2055,1590,290,35)]:
    for i in range(7):
        t0=i/7;t1=(i+1)/7
        x0=bx+lean*t0;y0=by-height*t0;x1=bx+lean*t1;y1=by-height*t1
        d.line([(x0,y0),(x1,y1+5)],fill=(62,83,72,70),width=max(2,6-i//2))
        if i in (2,4,6):
            sign=-1 if i%4==0 else 1
            ex=x1+sign*(50+i*5);ey=y1-30
            d.line([(x1,y1),(ex,ey)],fill=(62,83,72,58),width=2)
            for j in range(5):
                tx=x1+(ex-x1)*(j+1)/6;ty=y1+(ey-y1)*(j+1)/6
                dx=sign*random.uniform(20,42);dy=random.uniform(-33,26)
                d.polygon([(tx,ty),(tx+dx*.40-3,ty+dy*.65),(tx+dx,ty+dy),(tx+dx*.44+3,ty+dy*.32)],fill=(58,79,68,random.randint(48,90)))
canvas=Image.alpha_composite(canvas,layer.filter(ImageFilter.GaussianBlur(.45)))
canvas.convert('RGB').save(ART/'landscape-v1.png')

print(ART)
