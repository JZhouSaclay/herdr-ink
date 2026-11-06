"""Self-drawn single-cell ink cursor artwork. No external image sources."""
from pathlib import Path
import math,random
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
DEST=Path('/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/art')
DEST.mkdir(exist_ok=True,parents=True)
S=5;W,H=32,64

def art(phase=0,stroke=False):
 im=Image.new('RGBA',(W*S,H*S));d=ImageDraw.Draw(im)
 rng=random.Random(417)
 if stroke:
  # Narrow dry-brush stroke, heavier at the top, with split bristle endings.
  for k in range(20):
   x=8+rng.random()*7;y=9+rng.random()*4
   points=[((x+math.sin(t*.13+k)*.55)*S,(y+t)*S) for t in range(42-int(k*.25))]
   d.line(points,fill=(55,72,58,int(150+rng.random()*80)),width=max(1,int(rng.uniform(.22,.8)*S)))
 else:
  # Seven tiny leaves at different heights, drifting down inside one cell.
  # Fade at both edges so looping never produces a visible jump.
  for k in range(7):
   t=(phase/24+k/7)%1
   y=-5+t*74
   x=5+(k*7%22)+2.1*math.sin(t*math.tau+k*1.7)
   fade=min(1,max(0,(y+2)/7),max(0,(66-y)/8))
   if not fade:continue
   width=2.0+(k%3)*.65;height=4.2+(k%3)*.9
   angle=math.radians(-35+25*math.sin(t*math.tau+k))
   shape=[]
   for u,v in [(0,-height/2),(width/2,-height*.1),(width*.22,height*.22),(0,height/2),(-width*.48,height*.08),(-width*.35,-height*.23)]:
    shape.append(((x+u*math.cos(angle)-v*math.sin(angle))*S,(y+u*math.sin(angle)+v*math.cos(angle))*S))
   d.polygon(shape,fill=(52,74,54,round((190+(k%3)*18)*fade)))
 # Irregular paper absorption: keep the shape, soften pigment density.
 pixels=im.load()
 for y in range(H*S):
  for x in range(W*S):
   red,green,blue,alpha=pixels[x,y]
   if alpha:pixels[x,y]=(red,green,blue,round(alpha*rng.uniform(.85,1)))
 return im.resize((W,H),Image.Resampling.LANCZOS)
frames=[art(i) for i in range(24)]
for i,im in enumerate(frames):im.save(DEST/f'cursor-leaf-{i:02}.png')
art(stroke=True).save(DEST/'cursor-ink.png')
font=ImageFont.truetype(str(R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf'),30)
small=ImageFont.truetype(str(R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf'),20)
preview=[]
for leaf in frames:
 canvas=Image.new('RGB',(680,230),'#fbfaf7');d=ImageDraw.Draw(canvas)
 d.text((24,18),'细碎落叶 · 一格内持续飘落',font=font,fill='#384c3c')
 d.rounded_rectangle((22,70,658,148),radius=8,outline='#81907e',width=1)
 d.text((40,82),'竹影疏处，留白有声',font=font,fill='#3a433b')
 canvas.paste(leaf.resize((24,48),Image.Resampling.LANCZOS),(190,80),leaf.resize((24,48),Image.Resampling.LANCZOS))
 d.text((24,177),'墨痕（静态）',font=small,fill='#52624f')
 ink=art(stroke=True).resize((24,48));canvas.paste(ink,(175,162),ink)
 preview.append(canvas)
preview[0].save(R/'ink-cursor-leaf-preview.gif',save_all=True,append_images=preview[1:],duration=100,loop=0)
preview[0].save(R/'ink-cursor-leaf-preview.png')
print('Generated 24 particle frames, static ink stroke and preview.')
