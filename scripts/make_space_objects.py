"""Paint original desk-object miniatures with pressure, bristles and ink washes.
No vector bevels, object shadows or material gradients; transparent ink on paper.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

R = Path(__file__).resolve().parents[1]
A = R / 'mods/ink-chrome/art'
S = 5
N = 64*S
rng = np.random.default_rng(1601)


def curve(points):
    if len(points) == 2:
        return np.linspace(points[0], points[1], 100)
    p = np.array([points[0]] + list(points) + [points[-1]], dtype=float)
    out = []
    for a, b, c, d in zip(p, p[1:], p[2:], p[3:]):
        for t in np.linspace(0, 1, 35, endpoint=False):
            out.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return np.array(out+[p[-2]])


class Ink:
    def __init__(self, seed):
        self.rng = np.random.default_rng(seed)
        self.alpha = np.zeros((N, N), dtype=float)
        noise = Image.fromarray(self.rng.integers(0,256,(80,80),dtype='uint8'))
        self.paper = np.asarray(noise.resize((N,N),Image.Resampling.BICUBIC),dtype=float)/255

    def layer(self, mask, density, dry=0):
        a = np.asarray(mask,dtype=float)/255
        # Wet pigment collects unevenly; dry passages leave exposed paper.
        grain = .86 + .20*self.paper
        if dry:
            grain *= np.where(self.paper < dry*.65, .35, 1)
        a = np.clip(a*grain*density*1.12,0,.98)
        self.alpha = 1-(1-self.alpha)*(1-a)

    def stroke(self, points, width=2.4, density=.8, dry=.16, taper=.3):
        ps = curve(points)
        mask = Image.new('L',(N,N)); d=ImageDraw.Draw(mask)
        for i, (x,y) in enumerate(ps):
            t=i/(len(ps)-1)
            pressure=(1-taper)+taper*math.sin(math.pi*t)**.45
            pressure *= 1+.16*math.sin(t*15)+.08*math.sin(t*37)
            r=width*S*.59*pressure
            jitter=self.rng.normal(0,.07,2)*S
            x=x*S+jitter[0]; y=y*S+jitter[1]
            d.ellipse((x-r,y-r,x+r,y+r),fill=255)
        # Bristle separation follows the stroke direction instead of a uniform filter.
        for strand in range(max(1,int(width*.45))):
            offset=(strand/max(1,int(width*.45))-.5)*width*.8
            shifted=[]
            for i,p in enumerate(ps):
                tangent=ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)]
                norm=np.array([-tangent[1],tangent[0]])/(np.linalg.norm(tangent)+1e-5)
                q=(p+norm*offset)*S
                shifted.append(tuple(q))
            start=int(self.rng.uniform(.2,.5)*len(ps)); end=int(self.rng.uniform(.65,.99)*len(ps))
            if dry>.2 and width>2.5:
                d.line(shifted[start:end],fill=int(255*self.rng.uniform(.45,.8)),width=max(1,int(S*.17)))
        # Slight feathering retains ragged brush edges at the final display size.
        mask=mask.filter(ImageFilter.GaussianBlur(.16*S))
        self.layer(mask,density,dry)

    def wash(self, points, density=.14):
        mask=Image.new('L',(N,N));d=ImageDraw.Draw(mask)
        d.polygon([(x*S,y*S) for x,y in points],fill=240)
        mask=mask.filter(ImageFilter.GaussianBlur(.65*S))
        self.layer(mask,density)

    def ellipse(self, cx,cy,rx,ry,width=2,density=.7,partial=(0,2*math.pi)):
        p=[(cx+rx*math.cos(t),cy+ry*math.sin(t)) for t in np.linspace(*partial,18)]
        self.stroke(p,width,density,.13,.18)

    def image(self):
        rgba=np.zeros((N,N,4),dtype='uint8');rgba[:,:,:3]=[43,54,47]
        rgba[:,:,3]=np.clip(self.alpha*255,0,255).astype('uint8')
        return Image.fromarray(rgba).resize((256,256),Image.Resampling.LANCZOS)


def paint(name, seed):
    b=Ink(seed); st=b.stroke; w=b.wash; el=b.ellipse
    if name in ('go-black','go-white'):
        # A loosely loaded brush describes the stone with paper showing through.
        if name=='go-black':
            for j in range(10):
                y=20+j*2.5; half=math.sqrt(max(0,1-((y-32)/16)**2))*23
                st([(32-half,y),(23,y-1.8),(40,y+1),(32+half,y-.4)],4.5,.45+j*.027,.28,.45)
            el(32,33,22,14,2.2,.85,(.1,3.7))
        else:
            w([(11,30),(20,20),(40,18),(54,30),(50,41),(26,47),(11,39)],.1)
            el(32,32,23,15,2.9,.72,(-.2,2.7))
            el(32,32,23,15,1.3,.44,(3.05,5.7))
            st([(15,40),(27,46),(44,42)],3,.25,.2)
    elif name=='brush':
        st([(44,8),(35,24),(26,41)],5,.30,.24)
        st([(46,7),(37,24),(28,40)],1.8,.87,.27)
        st([(41,9),(32,25),(24,39)],1.1,.58)
        st([(24,37),(29,41)],3,.93,.2)
        st([(26,42),(23,47),(15,55)],7.5,.9,.30,.85)
        st([(23,45),(19,53),(12,58)],1.1,.8,.2,.9)
        st([(43,7),(45,3),(48,4),(47,8)],.9,.55)
    elif name=='scroll':
        w([(13,17),(43,12),(51,43),(22,50)],.13)
        st([(12,17),(25,16),(43,12)],1.4,.62)
        st([(20,48),(36,45),(51,42)],1.7,.7)
        st([(10,13),(14,30),(20,50)],5.8,.44,.24)
        st([(43,9),(47,24),(52,45)],5.5,.52,.25)
        st([(9,13),(13,29),(19,50)],1.4,.8)
        st([(43,9),(46,24),(52,45)],1.5,.82)
        for x,y in [(23,24),(31,22),(25,32),(33,30)]:
            st([(x,y),(x+3,y+1),(x+1,y+4)],1.3,.57,.2)
        st([(30,17),(32,29),(36,46)],.85,.51)
    elif name=='inkstone':
        w([(13,17),(28,12),(49,17),(52,43),(34,51),(13,45)],.46)
        st([(13,18),(12,39),(17,47),(35,51),(52,43),(50,19),(33,12),(17,16)],3.7,.8,.23)
        el(32,28,13,9,3.2,.87)
        st([(21,39),(34,42),(44,38)],2,.64)
        st([(43,8),(36,22),(31,32)],6,.82,.3)
    elif name=='fan':
        w([(6,24),(14,16),(28,10),(44,13),(57,23),(32,54)],.11)
        st([(6,24),(16,15),(30,11),(44,14),(57,23)],2.3,.78)
        for x,y in [(6,24),(17,16),(29,11),(43,14),(57,23)]:
            st([(x,y),(31,52)],1.3 if x in (6,57) else .85,.68,.19,.6)
        st([(18,27),(26,24),(40,26)],2.4,.32,.28)
        st([(30,49),(32,55)],3.4,.85)
    elif name=='cup':
        w([(12,25),(18,43),(32,47),(46,41),(52,24)],.12)
        el(32,24,20,7,2.7,.72)
        st([(12,25),(17,39),(26,46),(38,46),(47,37),(52,25)],3.5,.76,.21)
        st([(20,28),(32,30),(45,26)],3.1,.38,.26)
        st([(26,49),(35,50),(40,47)],1.7,.6)
    elif name=='seal':
        w([(14,30),(40,24),(50,32),(48,49),(25,55),(14,47)],.2)
        for p in [[(14,30),(25,37),(50,31)],[(14,30),(14,47),(25,55),(49,49),(50,31)],[(25,37),(25,54)],[(23,27),(23,18),(29,10),(37,12),(40,24)]]:
            st(p,2.8,.8,.22)
        st([(29,23),(30,17),(35,17)],2,.48)
    elif name=='gourd':
        w([(28,11),(38,13),(39,25),(48,39),(44,51),(29,55),(17,48),(16,37),(25,25),(23,17)],.2)
        st([(27,11),(23,17),(26,25),(17,34),(16,44),(23,53),(38,54),(47,45),(47,36),(39,26),(41,18),(37,12)],2.6,.78,.25)
        st([(30,11),(31,5),(38,6)],2,.83)
        st([(25,26),(33,29),(41,26)],1.6,.84)
        st([(33,29),(39,34),(45,48)],1.1,.55)
    elif name=='flute':
        st([(48,7),(17,54)],6,.23,.25)
        st([(46,5),(32,26),(15,53)],1.7,.8)
        st([(51,8),(35,32),(20,57)],1.7,.71)
        for x,y in [(43,15),(38,22),(33,30),(28,38),(22,46)]:
            st([(x,y),(x+3,y+2)],2.2,.89,.15)
        st([(22,47),(33,49),(34,58)],1.1,.62)
    elif name=='lantern':
        w([(20,14),(44,15),(53,30),(44,47),(19,47),(10,31)],.1)
        st([(19,14),(11,28),(15,40),(20,47)],2.3,.71)
        st([(45,15),(52,29),(48,42),(44,47)],2.6,.72)
        for x in (24,32,40):st([(x,16),(x+(-2 if x<32 else 2),31),(x,45)],.8,.38)
        st([(18,14),(31,13),(46,15)],3,.89)
        st([(19,47),(32,49),(45,47)],3,.85)
        st([(28,12),(28,6),(34,4),(37,12)],1.2,.68)
        st([(32,50),(32,58)],2,.74,.3)
    elif name=='book':
        w([(14,14),(46,10),(51,45),(18,52)],.16)
        st([(14,14),(30,12),(46,10),(50,45),(34,49),(18,52),(14,14)],2.5,.74,.23)
        st([(20,15),(22,31),(25,48)],1.2,.61)
        for y in (20,28,37,44):st([(15+(y-20)*.1,y),(22+(y-20)*.1,y-1)],1.1,.84)
        st([(35,17),(41,16),(43,32),(37,33),(35,17)],.9,.65)
        st([(39,20),(40,29)],1.3,.7)
        st([(21,54),(36,51),(52,47)],1.5,.44)
    elif name=='paperweight':
        w([(7,35),(46,21),(57,28),(17,45)],.15)
        st([(7,35),(27,29),(46,21),(57,28),(36,36),(17,45),(7,40)],2.1,.78,.24)
        st([(8,35),(17,40),(57,27)],1.3,.57)
        st([(17,40),(17,45)],1.7,.65)
        st([(28,31),(38,27),(44,28)],1.6,.31,.25)
    elif name=='lotus':
        for ps in [[(31,45),(17,38),(12,22),(26,27),(31,45)],[(32,45),(47,36),(53,21),(38,27),(32,45)],[(32,44),(22,28),(31,10),(42,27),(32,44)]]:
            w(ps,.09);st(ps,1.8,.65,.16,.65)
        st([(32,39),(31,19)],1.1,.39)
        st([(12,42),(23,52),(38,53),(51,41)],4,.53,.25)
    elif name=='pouch':
        w([(23,18),(41,17),(39,26),(48,38),(44,51),(30,55),(18,49),(16,38),(25,26)],.18)
        st([(23,18),(25,26),(17,37),(17,46),(26,54),(39,54),(48,45),(47,35),(40,26),(42,17)],2.5,.7,.25)
        st([(23,17),(33,20),(43,17)],2.6,.82)
        st([(24,25),(33,27),(42,24)],1.5,.85)
        st([(30,29),(24,39),(25,47)],1.7,.34)
        st([(40,25),(51,29),(52,43),(56,47)],1.1,.7)
    return b.image()


names=['go-black','brush','scroll','inkstone','fan','cup','seal','gourd','flute','lantern','go-white','book','paperweight','lotus','pouch']
board=Image.new('RGB',(750,300),'#f8faf8');d=ImageDraw.Draw(board)
for i,name in enumerate(names):
    im=paint(name,1601+i*17)
    im.save(A/f'object-v16-{name}.png')
    x,y=(i%5)*150+39,(i//5)*100+4
    obj=im.resize((72,72),Image.Resampling.LANCZOS);board.paste(obj,(x,y),obj)
    small=im.resize((24,24),Image.Resampling.LANCZOS);board.paste(small,(x+66,y+46),small)
    d.text((x+36,y+78),name,fill='#465348',anchor='mt')
board.save(R/'space-objects-v16.png')
print('Painted 15 original ink-brush miniatures; montage includes actual 24px samples')
