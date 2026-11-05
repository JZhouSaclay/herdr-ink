"""A quiet bamboo branch in the upper-left margin, preserving the v17 landscape."""
from pathlib import Path
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
R=Path(__file__).resolve().parents[1];A=R/'mods/ink-chrome/art'
base=Image.open(A/'landscape-v11.png').convert('RGBA');W,H=base.size
layer=Image.new('L',(W,H));d=ImageDraw.Draw(layer)
# The branch leans into the empty reading gutter; its tip stops before body text.
random.seed(1806)
for points,width,opacity in [([(25,-20),(45,62),(82,141),(125,217),(181,278),(209,300)],5,34),
                             ([(82,141),(131,149),(181,171),(227,187)],3,30),
                             ([(125,217),(103,257),(80,302)],3,24),
                             ([(45,62),(90,62),(135,78)],3,27)]:
    for i in range(len(points)-1):d.line(points[i:i+2],fill=opacity,width=max(1,width-i))
for x,y,dx,dy,width,alpha in [
    (49,73,10,62,10,27),(60,103,54,-3,12,35),(80,139,-25,58,11,27),
    (108,150,18,-60,12,31),(137,157,61,-25,13,33),(176,173,49,23,10,27),
    (194,183,35,-17,8,23),(128,220,45,29,11,32),(148,239,5,58,10,29),
    (177,274,47,-2,11,29),(195,289,26,42,10,24),(100,264,-40,14,10,26),
    (86,290,-8,42,8,22),(91,63,26,-37,9,29),(119,73,44,11,10,25)]:
    length=math.hypot(dx,dy);nx,ny=-dy/length*width,dx/length*width
    # Curved lanceolate leaf silhouette with a pin-point tip.
    pts=[(x,y),(x+dx*.34+nx*.6,y+dy*.34+ny*.6),
         (x+dx*.66+nx*.32,y+dy*.66+ny*.32),(x+dx,y+dy),
         (x+dx*.48-nx*.4,y+dy*.48-ny*.4)]
    d.polygon(pts,fill=alpha)
arr=np.asarray(layer,dtype=float);yy,xx=np.indices(arr.shape)
grain=np.clip(.87+.11*np.sin(xx*.57+yy*.11)+.07*np.sin(xx*.23-yy*.77),.6,1)
arr*=grain
layer=Image.fromarray(np.clip(arr,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(.42))
branch=Image.new('RGBA',(W,H),(63,84,69,0));branch.putalpha(layer)
# Keep the new decoration separately as well as composing the background.
branch.crop((0,0,300,390)).save(A/'bamboo-corner-v18.png')
base.alpha_composite(branch);base.convert('RGB').save(A/'landscape-v18.png')
base.crop((0,0,420,480)).convert('RGB').save(R/'bamboo-corner-v18-preview.png')
print('Generated upper-left pale bamboo; existing lower-right landscape remains unchanged.')
