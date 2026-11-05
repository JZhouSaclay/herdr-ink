"""Original dry-brush footer drawings for the native terminal image layer."""
from pathlib import Path
import math, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R=Path(__file__).resolve().parents[1]
A=R/'mods/ink-chrome/art'; F=R/'mods/ink-chrome/fonts'
INK=(65,82,70)

def stroke(points,width):
    # One continuous tapered brush contour, with a slightly dry, uneven edge.
    samples=[]
    for i in range(len(points)-1):
        a,b=points[i:i+2]
        for n in range(8):
            t=n/8
            samples.append((a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t))
    samples.append(points[-1]); left=[];right=[]
    for i,(x,y) in enumerate(samples):
        before=samples[max(0,i-1)];after=samples[min(len(samples)-1,i+1)]
        dx,dy=after[0]-before[0],after[1]-before[1];length=math.hypot(dx,dy) or 1
        t=i/(len(samples)-1)
        radius=width*.76*(.25+.75*math.sin(math.pi*t)**.38)*(1+.12*math.sin(i*1.7))
        left.append((x-dy/length*radius,y+dx/length*radius))
        right.append((x+dy/length*radius,y-dx/length*radius))
    return left+right[::-1]

# Coordinates are a shared 1000-square drawing surface. No stock icon library.
scroll=[stroke([(120,700),(130,240),(180,160),(440,130),(500,190),(540,140),(820,170),(870,250),(880,700)],39),
        stroke([(120,700),(280,650),(450,660),(500,730),(560,660),(740,650),(880,700)],36),
        stroke([(500,190),(490,390),(510,730)],30),
        stroke([(210,300),(410,280)],27),stroke([(210,420),(410,400)],27),
        stroke([(600,290),(790,310)],27),stroke([(610,410),(790,440)],25)]
# Three wind strokes and a long pointed leaf give speed a calm, legible silhouette.
wind=[stroke([(100,290),(360,250)],29),stroke([(80,450),(280,430)],25),
      stroke([(170,620),(350,590)],22),
      [(310,710),(405,490),(590,310),(910,170),(760,480),(550,640)],
      stroke([(335,735),(540,520),(820,260)],21)]
model=[stroke([(500,100),(490,370),(780,480),(510,570),(500,900),(390,570),(160,490),(410,380),(500,100)],40)]
shapes={'scroll':scroll,'wind':wind,'model':model}
chars={'🧠':'scroll','⚡':'wind','✦':'model'}
# Render above display resolution, then downsample to preserve feathered edges.
for kind,polys in shapes.items():
    body=''.join('<path d="M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in p)+'Z"/>' for p in polys)
    (A/f'footer-{kind}-v18.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><g fill="#415246">{body}</g></svg>\n')
    mask=Image.new('L',(512,512));draw=ImageDraw.Draw(mask)
    for polygon in polys:draw.polygon([(24+x*.464,24+y*.464) for x,y in polygon],fill=255)
    alpha=np.asarray(mask,dtype=float);y,x=np.indices(alpha.shape)
    grain=np.clip(.87+.10*np.sin(x*.59+y*.17)+.09*np.sin(x*.83-y*.44),.55,1)
    alpha*=grain
    image=Image.new('RGBA',mask.size,INK+(0,));image.putalpha(Image.fromarray(alpha.astype('uint8')))
    image.resize((96,96),Image.Resampling.LANCZOS).save(A/f'footer-{kind}-v18.png')
preview=Image.new('RGBA',(960,330),(252,252,249,255));draw=ImageDraw.Draw(preview)
for i,kind in enumerate(shapes):
    icon=Image.open(A/f'footer-{kind}-v18.png').resize((230,230),Image.Resampling.LANCZOS)
    preview.alpha_composite(icon,(40+i*320,20));draw.text((100+i*320,278),kind,fill=INK)
preview.convert('RGB').save(R/'footer-icons-v18.png')
print('Generated three original dry-brush footer drawings as transparent PNG and SVG.')
