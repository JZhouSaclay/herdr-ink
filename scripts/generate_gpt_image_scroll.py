"""Use the user's registered Magpie GPT Image 2 image endpoint, not chat models."""
from pathlib import Path
import re,json,urllib.request,time,traceback
R=Path(__file__).resolve().parents[1];D=R/'candidates/gpt-image-2-scroll';D.mkdir(exist_ok=True)
MODEL='codex/gpt-image-2'
prompt='''请绘制一张适合软件侧栏使用的中国水墨简笔画素材：正面平视、竖向完整展开的空白书卷，一张修长的宣纸，上下各有一根细长的横向卷轴，轴头仅稍微伸出纸边。整体像一幅未题字的中国挂轴。纸面接近中性灰白色（#f7f8f3），纸边是自然手绘的极淡灰墨线，少量飞白；卷轴以灰墨几笔带过，保留轻微纸张卷曲，灰黑轴头细小克制，不要厚重木头，不要棕黄做旧。中央至少85%的区域完全空白而平整，用于叠加软件文件列表及代码，不要山水、文字、印章、花鸟、人物或任何图案。上下卷轴的轮廓清楚但轻盈。背景完全透明，独立书卷，四周留少量空白，不要投影光晕、透视、照片或立体渲染。简笔写意，清淡、安静，与水墨风格的软件界面相配。请采用竖向构图。'''
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
