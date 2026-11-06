"""Render the user-supplied ink SVG into a right-to-left falling cursor loop."""
from pathlib import Path
from io import BytesIO
import math,random,subprocess,json,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
SVG=R/'reference/cursor-willow-D.svg'
DEST=Path('/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/art')
S=5;W,H=64,64

# Rasterize the actual SVG paths; retain the original ink density and edges.
source=Image.open(BytesIO(subprocess.check_output(['resvg','-w','999',str(SVG),'-c']))).convert('RGBA')
source=source.crop(source.getbbox())

def trajectory(phase,k):
 t=(phase/24+k/7)%1
 lane=(k%5-2)*6
 x=74-84*t+lane+2.4*math.sin(t*math.tau+k*1.7)
 y=-10+84*t+lane+1.3*math.sin(t*math.tau+k*.7)
 return t,x,y

def art(phase=0,stroke=False):
 canvasWidth=32 if stroke else W
 im=Image.new('RGBA',(canvasWidth*S,H*S))
 if stroke:
  d=ImageDraw.Draw(im);rng=random.Random(417)
  for k in range(20):
   x=8+rng.random()*7;y=9+rng.random()*4
   points=[((x+math.sin(t*.13+k)*.55)*S,(y+t)*S) for t in range(42-int(k*.25))]
   d.line(points,fill=(55,72,58,int(150+rng.random()*80)),width=max(1,int(rng.uniform(.22,.8)*S)))
  pixels=im.load()
  for y in range(H*S):
   for x in range(canvasWidth*S):
    red,green,blue,alpha=pixels[x,y]
    if alpha:pixels[x,y]=(red,green,blue,round(alpha*rng.uniform(.85,1)))
 else:
  for k in range(7):
   t,x,y=trajectory(phase,k)
   fade=min(1,max(0,min(x+7,y+7,W+7-x,H+7-y)/13))
   if fade<=0:continue
   width=26+(k%3)*4
   leaf=source.resize((round(width*S),round(width*S*source.height/source.width)),Image.Resampling.LANCZOS)
   # Small changes in angle let the painted leaf turn in the breeze.
   leaf=leaf.rotate(-10+18*math.sin(t*math.tau+k*.8),Image.Resampling.BICUBIC,expand=True)
   leaf.putalpha(leaf.getchannel('A').point(lambda a:round(255*(a/255)**.68*fade)))
   im.alpha_composite(leaf,(round(x*S-leaf.width/2),round(y*S-leaf.height/2)))
 return im.resize((canvasWidth,H),Image.Resampling.LANCZOS)

DEST.mkdir(exist_ok=True,parents=True)
frames=[art(i) for i in range(24)]
for i,im in enumerate(frames):im.save(DEST/f'cursor-leaf-{i:02}.png')
art(stroke=True).save(DEST/'cursor-ink.png')
font=ImageFont.truetype(str(R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf'),30)
small=ImageFont.truetype(str(R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf'),20)
preview=[]
for leaf in frames:
 canvas=Image.new('RGB',(680,250),'#fbfaf7');d=ImageDraw.Draw(canvas)
 d.text((24,18),'水墨柳叶 · 右上向左下飘落',font=font,fill='#384c3c')
 d.rounded_rectangle((22,70,658,148),radius=8,outline='#81907e',width=1)
 d.text((40,82),'竹影疏处，留白有声',font=font,fill='#3a433b')
 sprite=leaf.resize((30,48),Image.Resampling.LANCZOS);canvas.paste(sprite,(190,80),sprite)
 d.text((24,174),'叶形取自指定 SVG，保留浓淡笔触',font=small,fill='#52624f')
 thumb=source.copy();thumb.thumbnail((85,65),Image.Resampling.LANCZOS);canvas.paste(thumb,(540,166),thumb)
 preview.append(canvas)
preview[0].save(R/'ink-cursor-leaf-preview.gif',save_all=True,append_images=preview[1:],duration=100,loop=0)
preview[0].save(R/'ink-cursor-leaf-preview.png')
# Verify each leaf drifts left and down between wrap points, not straight down.
for k in range(7):
 for phase in range(23):
  t,x,y=trajectory(phase,k);nt,nx,ny=trajectory(phase+1,k)
  if nt>t:assert nx<x and ny>y,(phase,k)
coverage=[sum(a>40 for a in im.getchannel('A').getdata())/(W*H) for im in frames]
(R/'ink-leaf-art-verification.json').write_text(json.dumps({'source':'reference/cursor-willow-D.svg','source_sha256':hashlib.sha256(SVG.read_bytes()).hexdigest(),'rendered_from_svg':True,'source_crop_size':source.size,'frames':24,'leaf_count':7,'direction':'upper-right to lower-left','all_non_wrap_steps_left_and_down':True,'coverage_min':min(coverage),'coverage_max':max(coverage)},indent=2)+'\n')
print('Rendered 24 frames from the supplied SVG; every trajectory moves left and down.')
