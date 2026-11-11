"""Extract actual generated art; trace grey washes into real SVG paths."""
from pathlib import Path
import sys,json,re,subprocess
import numpy as np
from scipy import ndimage
from PIL import Image,ImageFont,ImageDraw
R=Path(__file__).resolve().parents[1];D=R/'candidates/ink-generation-D-F';sys.path.insert(0,str(R/'.image-tools'))
import vtracer
outputs={}
for name,source in [('D','D2'),('F','F')]:
 original=Image.open(D/f'{source}-generated-original.png').convert('RGB')
 if name=='D':original=original.crop((325,85,675,365))
 rgb=np.asarray(original,dtype=float);lum=rgb.mean(2)
 red=(rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,0]>rgb[:,:,2]*1.35)
 ink=(lum<247)&~red
 if name=='F':ink[:,640:]=False  # exclude the model-generated decorative stamp, outside the feather
 labels,count=ndimage.label(ink);sizes=np.bincount(labels.ravel());keep=sizes>=12;keep[0]=False;ink=keep[labels]
 alpha=np.clip((255-lum)/225*255,0,255);alpha[~ink]=0
 rgba=np.zeros((*lum.shape,4),dtype='uint8');rgba[:,:,:3]=[30,37,30];rgba[:,:,3]=alpha.astype('uint8')
 clean=Image.fromarray(rgba);bbox=clean.getbbox();clean=clean.crop(bbox)
 padded=Image.new('RGBA',(clean.width+32,clean.height+32));padded.alpha_composite(clean,(16,16));padded.save(D/f'{name}-ink-transparent.png')
 # Keep RGB grey washes for the tracer, with a genuinely transparent outside.
 trace=np.array(original.convert('RGBA'));trace[:,:,:3]=np.repeat(lum.astype('uint8')[:,:,None],3,axis=2);trace[:,:,3]=np.where(ink,255,0).astype('uint8')
 trace=Image.fromarray(trace).crop(bbox);canvas=Image.new('RGBA',padded.size);canvas.alpha_composite(trace,(16,16))
 canvas.save(D/f'{name}-tracer-input.png')
 cfg=vtracer.Config(clustering='color-cluster',hierarchical='cutout',mode='spline',filter_speckle=5,color_precision=6,layer_difference=10,max_colors=16,simplify=.55,path_precision=2)
 raw=cfg.convert_pixels(canvas.tobytes(),canvas.width,canvas.height)
 # Traced grey fills become translucent ink, keeping the paper outside empty.
 def inkfill(m):
  color=m[1];r,g,b=[int(color[i:i+2],16) for i in (0,2,4)];opacity=max(0,min(1,(255-(r+g+b)/3)/225))
  return f'fill="#1e251e" fill-opacity="{opacity:.4f}"'
 raw=re.sub(r'fill="#([0-9A-Fa-f]{6})"',inkfill,raw)
 svg=D/f'{name}-ink-vector.svg';svg.write_text(raw)
 assert '<image' not in raw and '<path' in raw,'SVG must contain real paths, not embedded bitmaps'
 subprocess.run(['rsvg-convert',str(svg),'-o',str(D/f'{name}-svg-render.png')],check=True)
 outputs[name]={'source':f'{source}-generated-original.png','png':f'{name}-ink-transparent.png','svg':svg.name,'path_count':raw.count('<path'),'embedded_bitmap':False,'dimensions':list(padded.size)}

paper=(248,250,247);board=Image.new('RGB',(1280,1060),paper);draw=ImageDraw.Draw(board)
face=R/'mods/ink-chrome/fonts/LXGWWenKaiMono-Regular.ttf';title=ImageFont.truetype(str(face),32);label=ImageFont.truetype(str(face),22);small=ImageFont.truetype(str(face),19)
draw.text((34,22),'真实生图 · 柳叶 D / 鹤羽 F',font=title,fill=(38,51,40))
draw.text((35,69),'FLUX.1 Schnell 生成原画 → 主体去底 → 灰阶路径 SVG；当前标记未替换。',font=small,fill=(94,109,98))
for i,name in enumerate(['D','F']):
 x=i*640;draw.text((x+34,121),'D  柳叶' if name=='D' else 'F  鹤羽',font=title,fill=(37,52,40))
 for j,(filename,caption) in enumerate([(f'{name}-ink-transparent.png','去底后的生成画作'),(f'{name}-svg-render.png','SVG 转换效果')]):
  im=Image.open(D/filename).convert('RGBA');im.thumbnail((490,330),Image.Resampling.LANCZOS)
  xx=x+int((640-im.width)/2);yy=(174 if j==0 else 568)+int((330-im.height)/2)
  board.paste(im,(xx,yy),im);draw.text((x+34,516 if j==0 else 911),caption,font=label,fill=(89,105,93))
 bamboo=Image.open(R/'mods/ink-chrome/art/bamboo-v9-136.png').convert('RGBA').resize((320,94),Image.Resampling.LANCZOS)
 mark=Image.open(D/f'{name}-svg-render.png').convert('RGBA');mark.thumbnail((40,36),Image.Resampling.LANCZOS);bamboo.alpha_composite(mark,(24+(40-mark.width)//2,28+(36-mark.height)//2))
 td=ImageDraw.Draw(bamboo);td.text((79,28),'何德',font=ImageFont.truetype(str(face),28),fill=(40,52,43))
 board.paste(bamboo,(x+270,950),bamboo);draw.text((x+34,980),'标签示意（2×）',font=small,fill=(105,117,108))
board.save(D/'D-F-generated-comparison.png');board.save(R/'generated-D-F-preview-v21.png')
(D/'generation-manifest.json').write_text(json.dumps({'provider':'Hugging Face public Space','model':'black-forest-labs/FLUX.1-schnell','steps':4,'generated_resolution':[768,768],'outputs':outputs,'installed':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(outputs,ensure_ascii=False))
