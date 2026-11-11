"""Use the user's registered Magpie GPT Image 2 image endpoint, not chat models."""
from pathlib import Path
import re,json,urllib.request,time,traceback
R=Path(__file__).resolve().parents[1];D=R/'candidates/gpt-image-2-crane-feather';D.mkdir(exist_ok=True)
MODEL='codex/gpt-image-2'
prompt='''请创作一幅真正有笔墨气韵的中国水墨写意小品：仅有一根仙鹤羽毛，独立主体，背景干净纯白，四周留白。羽梗位于左下，羽轴向右上自然弯曲，形成优雅舒展的弧线；羽片一侧略宽、一侧略窄，有自然松散的羽丝和少数不规则缺口。用浓墨写出有力的羽轴与局部羽缘，灰墨和淡墨画出轻柔羽片，包含自然晕染、干笔飞白、纸上渗化和真实毛笔的细微变化。羽毛应轻盈而有骨力，黑白灰为主，不要彩色。整体轮廓干净明确，缩小为软件标签的小标记时仍能认出是羽毛。不要均匀重复的梳齿形羽丝，不要几何图标或矢量插画效果，不要画鸟、翅膀、叶子、其他物体、文字、印章、题款或装饰边框。构图不要裁切羽尖或羽梗。'''
(D/'request.json').write_text(json.dumps({'model':MODEL,'prompt':prompt,'response_format':'b64_json'},ensure_ascii=False,indent=2)+'\n')
(D/'status.json').write_text(json.dumps({'state':'generating','model':MODEL,'started':time.time()}))
try:
 s=Path('/Users/jiezhou/.pi/agent/extensions/magpie.ts').read_text();cfg=json.loads(re.search(r'const MAGPIE\s*=\s*(\{.*?\});',s,re.S)[1])
 assert MODEL in [m['id'] for m in cfg['images']]
 req=urllib.request.Request(cfg['baseUrl'].rstrip('/')+'/images/generations',data=json.dumps({'model':MODEL,'prompt':prompt,'response_format':'b64_json'},ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+cfg['apiKey']})
 with urllib.request.urlopen(req,timeout=300) as response:
  result=json.load(response)
 import base64
 from PIL import Image
 saved=[]
 for i,item in enumerate(result.get('data',[])):
  if item.get('b64_json'):raw=base64.b64decode(item['b64_json'])
  elif item.get('url'):
   with urllib.request.urlopen(item['url'],timeout=45) as r:raw=r.read()
  else:continue
  p=D/f'generated-{i+1}.png';p.write_bytes(raw)
  with Image.open(p) as im:im.verify()
  saved.append(p.name)
 if not saved:raise RuntimeError('Image endpoint returned no image data')
 (D/'status.json').write_text(json.dumps({'state':'complete','requested_model':MODEL,'returned_model':result.get('model'),'images':saved,'completed':time.time()},ensure_ascii=False,indent=2)+'\n')
 print('Saved',saved,flush=True)
except Exception as e:
 (D/'status.json').write_text(json.dumps({'state':'error','model':MODEL,'error':type(e).__name__+': '+str(e)},ensure_ascii=False,indent=2)+'\n')
 print(type(e).__name__,str(e),flush=True)
