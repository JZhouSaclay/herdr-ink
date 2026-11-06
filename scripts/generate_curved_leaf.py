"""Generate a curved ink willow leaf using Magpie's configured image model."""
from pathlib import Path
import urllib.request,urllib.error,json,base64,subprocess,datetime,sys,re
R=Path(__file__).resolve().parents[1]
MODEL=sys.argv[1] if len(sys.argv)>1 else 'codex/gpt-image-2'
OUT=R/'reference/gpt-image-curved-leaf-v4'
status=R/'.checkpoints/curved-leaf-generation-status.json'
def report(**data):status.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
prompt='''Use the reference image for the authentic Chinese ink-wash texture. Paint ONE isolated slender willow leaf, with a noticeably bowed, graceful C-shaped body and a gently hooked, finely tapering tip. The middle of the leaf should bow away from the straight line joining its tip and stem by about one fifth of its length. It should look light, flexible, caught in a soft breeze. A short delicate stem. Expressive real brushwork with rich dark ink accents, soft grey washes, restrained dry-brush gaps, organic asymmetric edges, subtle paper bleeding within the leaf. Retain enough contrast to read when reduced to a tiny animated cursor. Slender, curved and elegant rather than broad or chunky. Entire leaf fully visible with generous blank margins. Upper-right tip, lower-left stem, balanced diagonal composition. Pure clean white background, no paper texture in the background, no shadow, no writing, no seal, no border, no branch, no extra leaves, no feather. This is a hand-painted ink-wash art asset, not a flat vector icon or a geometric polygon.'''
ref=subprocess.check_output(['resvg','-w','666',str(R/'reference/cursor-willow-D.svg'),'-c'])
body={'model':MODEL,'prompt':prompt,'response_format':'b64_json','images':['data:image/png;base64,'+base64.b64encode(ref).decode()]}
OUT.with_suffix('.request.json').write_text(json.dumps({'model':MODEL,'prompt':prompt,'reference':'reference/cursor-willow-D.svg','route':'Magpie local images API','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2)+'\n')
report(state='generating',model=MODEL)
try:
 request=urllib.request.Request('http://127.0.0.1:3425/v1/images/generations',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer magpie'},method='POST')
 with urllib.request.urlopen(request,timeout=300) as response:result=json.load(response)
 images=result.get('data',[])
 if not images:raise RuntimeError('Image response contains no data')
 image=images[0]
 if image.get('b64_json'):data=base64.b64decode(image['b64_json'])
 elif image.get('url'):
  with urllib.request.urlopen(image['url'],timeout=60) as response:data=response.read()
 else:raise RuntimeError('Image response contains neither image bytes nor URL')
 OUT.with_suffix('.png').write_bytes(data)
 report(state='completed',model=MODEL,image=str(OUT.with_suffix('.png')),usage=result.get('usage'),completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
except Exception as error:
 message=str(error)
 if isinstance(error,urllib.error.HTTPError):
  try:message=json.loads(error.read()).get('error',{}).get('message',message)
  except Exception:pass
 message=re.sub(r'Bearer\s+\S+|sk-[\w-]+','[redacted]',message)[:600]
 report(state='failed',model=MODEL,error=message)
 sys.exit(1)
