"""Eight alternative ink tab marks; proposal artifacts only, no live layout edits."""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=Path(__file__).resolve().parents[1];OUT=R/'candidates/tab-marks-20261106';OUT.mkdir(parents=True,exist_ok=True)
S=28;SIZE=(20*S,18*S);PAPER=(248,250,247)
def cubic(a,b,c,d):
 return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1)) for t in np.linspace(0,1,100)]
def pts(p):return [(round(x*S),round(y*S)) for x,y in p]
def stroke(d,p,w=0.4,a=240):d.line(pts(p),fill=a,width=max(1,round(w*S)),joint='curve')
def poly(d,p,a=244):d.polygon(pts(p),fill=a)
def empty():return Image.new('L',SIZE)
def finish(mask,seed):
 a=np.asarray(mask.filter(ImageFilter.GaussianBlur(.026*S)),dtype=float);y,x=np.indices(a.shape);rng=np.random.default_rng(seed)
 wash=np.clip(.90+.06*np.sin(x*.075+y*.028)+.04*np.sin(y*.15-x*.041),.77,1)
 a*=wash;a[(rng.random(a.shape)>.993)&(a>90)]*=.45
 rgb=np.zeros((*a.shape,4),dtype='uint8');rgb[:,:,:3]=[36,49,40];rgb[:,:,3]=np.clip(a,0,255).astype('uint8')
 return Image.fromarray(rgb)
marks=[]
# A: Gingko fan: two rounded lobes, a visible notch and fine fan veins.
m=empty();d=ImageDraw.Draw(m)
shape=cubic((10,13.2),(5.8,11.8),(2.3,10.2),(1.4,6.2))+cubic((1.4,6.2),(1,2),(5.8,.2),(9.6,4))+cubic((9.6,4),(12,-.7),(18.3,1.4),(18.4,6.2))+cubic((18.4,6.2),(18.4,9.8),(14.5,12.3),(10,13.2))
poly(d,shape);stroke(d,cubic((10,12.5),(10,14),(9.2,15.5),(8.8,17)),.55)
for x,y in [(3.2,5),(6.3,2.8),(13.4,2.6),(17,5.6)]:stroke(d,cubic((10,12.5),(9.8,9),(x,7),(x,y)),.16,92)
marks.append(('A','银杏','扇形轮廓 · 饱满稳重',finish(m,1)))
# B: five-point maple with asymmetrical natural serrations.
m=empty();d=ImageDraw.Draw(m)
poly(d,[(9.2,14),(4,12.3),(4.8,10.8),(1,9.2),(3,8),(1.7,5),(5,6),(4.5,2.7),(7.3,4.4),(9.1,.5),(11.4,4.7),(14.6,2.3),(14.4,6.1),(18.4,4.9),(17.2,8.1),(19,9.3),(15.2,11),(15.5,12.8),(10.4,14)])
stroke(d,cubic((9.8,12),(10.4,14.3),(11.8,15.8),(12.8,17.4)),.6)
for end in [(9.1,2),(3.4,6.7),(16.8,7)]:stroke(d,cubic((9.8,13),(9.7,10),(end[0],8),end),.2,95)
marks.append(('B','枫叶','五角叶形 · 最易辨认',finish(m,2)))
# C: sparse bamboo, separate pressure-written leaves rather than a single solid blade.
m=empty();d=ImageDraw.Draw(m)
stroke(d,cubic((3,16.7),(6.7,12),(10.2,8),(13.8,3.2)),.48)
for a,b,c,e,ret1,ret2 in [((7,12),(1,10),(1,4),(2.6,1.5),(5.1,5.5),(6.6,8)),((8.5,10),(11,5),(15.9,4),(19,4.5),(16.7,7.6),(12.9,9.5)),((10.8,6.9),(8.2,3.6),(10,1.1),(12.6,.4),(12.5,3.3),(12,5.4))]:poly(d,cubic(a,b,c,e)+cubic(e,ret1,ret2,a))
marks.append(('C','疏竹','三笔竹叶 · 轻巧写意',finish(m,3)))
# D: a willow leaf, sweeping stem and very long point.
m=empty();d=ImageDraw.Draw(m)
poly(d,cubic((5,14.8),(5.8,7),(12,2),(17,.7))+cubic((17,.7),(13.8,6.1),(12.4,13.2),(5,14.8)),222)
stroke(d,cubic((3,17),(6.3,12.7),(11.8,5.1),(16.6,1.2)),.35)
stroke(d,cubic((6.1,13.4),(8.8,9.5),(12.5,4.2),(15.5,2.2)),.17,88)
marks.append(('D','柳叶','细长弯叶 · 留白最多',finish(m,4)))

def feather(base,tip,width,bend,seed,light=False,broken=False):
 m=empty();d=ImageDraw.Draw(m);b=np.array(base,dtype=float);v=np.array(tip,dtype=float)-b;length=np.linalg.norm(v);n=np.array([-v[1],v[0]])/length
 def center(t):return b+v*t+n*bend*math.sin(math.pi*t)
 def extent(t):return width*math.sin(math.pi*max(0,min(1,(t-.18)/.82)))**.65
 left=[];right=[]
 for t in np.linspace(.19,1,100):
  jag=.89+.11*math.sin(t*math.pi*32)
  left.append(tuple(center(t)+n*extent(t)*jag));right.append(tuple(center(t)-n*extent(t)*(.72 if light else .84)*jag))
 poly(d,left+right[::-1],165 if light else 243)
 # Sparse notches open toward the vane; the shaft stays continuous.
 for i,t in enumerate([.34,.48,.62,.77,.88] if broken else [.38,.59,.78]):
  side=1 if i%2 else -1;outer=center(t)+side*n*extent(t)*1.06
  inner=center(t-.09)+side*n*extent(t)*.20
  poly(d,[tuple(outer),tuple(inner),tuple(outer+v*.035)],0)
 # Barbs are broad brush filaments, visible as grey shifts, not an icon outline.
 for side in [-1,1]:
  for t in np.linspace(.29,.90,11):
   root=center(t-.08);edge=center(t)+side*n*extent(t)*(.84 if side>0 else .69)
   stroke(d,[tuple(root),tuple(edge)],.13,72 if not light else 117)
 stroke(d,[tuple(center(t)) for t in np.linspace(0,.98,80)],.43,245)
 if not light:stroke(d,[tuple(center(t)) for t in np.linspace(.24,.91,70)],.16,112)
 return m
# E: broad goose feather, dark quill.
marks.append(('E','雁羽','宽羽片 · 墨色醒目',finish(feather((2.2,16.8),(17.1,.8),3.5,.2,5),5)))
# F: a narrower, airier crane plume with a slightly curved shaft.
marks.append(('F','鹤羽','浅羽深轴 · 呼应仙鹤',finish(feather((4,17.1),(15.6,.6),2.9,1.3,6,light=True),6)))
# G: bold, broken feather with clear dry-brush separations.
m=feather((1.8,16.7),(18.1,4.1),4.15,-.6,7,broken=True);gd=ImageDraw.Draw(m)
for points,w in [([(5.7,13.5),(9.8,9.7),(12.3,5.1)],.55), ([(9.4,12.2),(14,10.9),(17,6.3)],.65), ([(11.4,13.7),(14.5,11.7)],.8)]:stroke(gd,points,w,0)
marks.append(('G','飞白翎','宽羽飞白 · 笔意更强',finish(m,7)))
# H: paired plumes, unequal lengths and tones.
a=feather((6,17.2),(7.5,.8),2.15,-1,8,light=True);b=feather((6,17.2),(18,4.1),2.0,.1,9)
m=Image.fromarray(np.maximum(np.asarray(a),np.asarray(b)))
marks.append(('H','双翎','一浓一淡 · 成对舒展',finish(m,8)))

fontpath=R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf'
font=ImageFont.truetype(str(fontpath),26);small=ImageFont.truetype(str(fontpath),19);label=ImageFont.truetype(str(fontpath),21)
sheet=Image.new('RGB',(1600,1000),PAPER);d=ImageDraw.Draw(sheet)
d.text((36,22),'标签标记候选 · 叶子与羽毛',font=ImageFont.truetype(str(fontpath),32),fill=(39,51,42))
d.text((37,67),'上排叶子，下排羽毛。每款包含放大图与 2× 屏幕示意；正式标记仍为 20 × 18。',font=small,fill=(100,112,102))
bamboo=Image.open(R/'mods/ink-chrome/art/bamboo-v9-136.png').convert('RGBA').resize((320,94),Image.Resampling.LANCZOS)
for i,(code,name,detail,im) in enumerate(marks):
 im.save(OUT/f'{code}-{name}.png')
 x=(i%4)*400;y=118+(i//4)*438
 d.text((x+28,y),f'{code}  {name}',font=font,fill=(35,49,40))
 hero=im.resize((180,162),Image.Resampling.LANCZOS);sheet.paste(hero,(x+108,y+47),hero)
 d.text((x+28,y+232),detail,font=small,fill=(100,112,102))
 # Display the actual indicator/title geometry at exactly twice native pixels.
 tab=Image.new('RGBA',(320,94));tab.alpha_composite(bamboo)
 mini=im.resize((40,36),Image.Resampling.LANCZOS);tab.alpha_composite(mini,(23,28))
 td=ImageDraw.Draw(tab);td.text((78,27),'何德',font=ImageFont.truetype(str(fontpath),28),fill=(46,57,48));td.line([(275,39),(289,53)],fill=(99,111,100),width=2);td.line([(289,39),(275,53)],fill=(99,111,100),width=2)
 sheet.paste(tab,(x+30,y+280),tab)
 d.text((x+30,y+386),'标签中的样子（2×）',font=small,fill=(117,126,118))
sheet.save(OUT/'候选总览.png');sheet.save(R/'tab-mark-candidates-v20.png')
# Two smaller sheets retain larger previews on narrow chat screens.
sheet.crop((0,0,1600,550)).save(OUT/'叶子候选.png')
feathers=Image.new('RGB',(1600,560),PAPER);feathers.paste(sheet.crop((0,0,1600,108)),(0,0));feathers.paste(sheet.crop((0,556,1600,1000)),(0,112));feathers.save(OUT/'羽毛候选.png')
(OUT/'说明.json').write_text(json.dumps({'slot':[20,18],'preview_scale':2,'installed':False,'options':[{'id':c,'name':n,'note':t,'file':f'{c}-{n}.png'} for c,n,t,_ in marks]},ensure_ascii=False,indent=2)+'\n')
print(OUT/'候选总览.png')
