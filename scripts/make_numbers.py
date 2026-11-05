"""Paint Arabic brush numerals 1–15 with pressure, dry edges and scan texture."""
from pathlib import Path
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];A=R/'mods/ink-chrome/art';S=3
# Handwritten centerlines in a 42 × 78 design space, shared across all numerals.
paths={
'0':[[(29,5),(14,8),(7,26),(6,50),(13,69),(27,70),(36,54),(37,30),(32,11),(23,6)]],
'1':[[(13,20),(26,7),(22,32),(18,70)],[(9,71),(29,71)]],
'2':[[(7,18),(16,7),(29,8),(36,18),(31,34),(18,48),(5,67),(21,69),(37,65)]],
'3':[[(8,10),(22,6),(34,13),(33,26),(20,36),(30,38),(36,49),(30,65),(17,70),(6,63)]],
'4':[[(30,5),(10,39),(5,47),(37,45)],[(29,28),(25,71)]],
'5':[[(36,7),(12,9),(9,34),(24,31),(35,40),(33,57),(23,69),(9,65),(5,60)]],
'6':[[(32,7),(17,17),(8,38),(7,57),(17,70),(31,65),(36,51),(28,39),(13,41),(8,51)]],
'7':[[(5,12),(22,7),(38,8),(27,31),(19,52),(13,72)]],
'8':[[(23,36),(9,25),(11,11),(24,6),(36,16),(31,30),(15,43),(6,57),(13,70),(28,69),(36,57),(32,46),(23,36)]],
'9':[[(32,33),(19,39),(7,28),(9,13),(23,7),(35,18),(34,36),(26,57),(14,72)]]}
def curve(points):
    # Catmull–Rom, interpolating the hand-drawn centerline points.
    p=[points[0]]+points+[points[-1]];out=[]
    for a,b,c,d in zip(p,p[1:],p[2:],p[3:]):
        for t in np.linspace(0,1,18,endpoint=False):out.append(tuple(.5*((2*b[j])+(-a[j]+c[j])*t+(2*a[j]-5*b[j]+4*c[j]-d[j])*t*t+(-a[j]+3*b[j]-3*c[j]+d[j])*t*t*t) for j in (0,1)))
    return out+[points[-1]]
for n in range(1,16):
    mask=Image.new('L',(128*S,96*S));d=ImageDraw.Draw(mask);text=str(n);left=(128-(len(text)*42+(len(text)-1)*7))/2
    for k,ch in enumerate(text):
        for stroke in paths[ch]:
            ps=curve(stroke)
            for i,(x,y) in enumerate(ps):
                t=i/max(1,len(ps)-1);pressure=1.7+1.5*math.sin(math.pi*t)+.55*math.sin(8*t+k)
                x=(left+k*49+x)*S;y=(9+y)*S
                d.ellipse((x-pressure*S/2,y-pressure*S/2,x+pressure*S/2,y+pressure*S/2),fill=235)
    alpha=np.array(mask.filter(ImageFilter.GaussianBlur(.27*S)),dtype=float)
    yy,xx=np.indices(alpha.shape);grain=.85+.10*np.sin(xx*.31+yy*.17)+.05*np.sin(xx*1.43-yy*.63)
    alpha=np.clip(alpha*grain,0,255).astype('uint8');rgb=np.zeros((*alpha.shape,4),dtype='uint8');rgb[:,:,:3]=[70,83,72];rgb[:,:,3]=alpha
    Image.fromarray(rgb).save(A/f'ink-number-v11-{n}.png')
board=Image.new('RGB',(750,200),(248,250,248))
for n in range(1,16):
    im=Image.open(A/f'ink-number-v11-{n}.png').resize((96,72),Image.Resampling.LANCZOS);board.paste(im,(((n-1)%8)*94,((n-1)//8)*98),im)
board.save(R/'ink-numbers-v11.png')
# Keep the scene behind conversation text fainter than navigation boundaries.
im=np.asarray(Image.open(A/'landscape-v2.png').convert('RGB'),dtype=float)
Image.fromarray(np.clip(im*.70+np.array([252,252,249])*.30,0,255).astype('uint8')).save(A/'landscape-v11.png')
print('Generated ink numbers 1–15 and a 30% lighter conversation landscape')
