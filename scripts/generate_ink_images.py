"""Call the official public FLUX Schnell demo; no account or private payload."""
from pathlib import Path
import json,urllib.request,sys
R=Path(__file__).resolve().parents[1];D=R/'candidates/ink-generation-D-F';D.mkdir(exist_ok=True)
BASE='https://black-forest-labs-flux-1-schnell.hf.space'
PROMPTS={
'D': 'Traditional Chinese ink wash painting on pure white paper: one single slender curved willow leaf with a short delicate stem. Diagonal composition from lower left to upper right, long graceful tapered point. Expressive natural brushwork by a skilled Chinese painter, black ink with subtle grey washes, dry-brush white gaps, slight ink bleeding on rice paper, minimal and elegant. The silhouette is simple and bold enough to recognize when reduced. Only ONE leaf, centered with generous white margin. No text, no writing, no seal, no border, no photograph, no vector logo, no geometric icon. Authentic sumi-e fine art.',
'F': 'Traditional Chinese ink wash painting on pure white paper: one single elegant crane feather, a gracefully curved dark quill from lower left toward upper right. Soft asymmetric feather vanes with irregular loose barbs and a few natural splits, black accents and translucent grey washes, expressive dry-brush white gaps and slight rice paper bleeding. A real hand-painted sumi-e artwork, simple clear silhouette and minimal composition, centered with generous white margins. Only ONE feather. No bird, no wing, no leaf, no text, no writing, no seal, no frame, no photograph, no vector logo, no repeating geometric teeth.'}
PROMPTS['D2']='A close-up ink wash study of ONE detached willow leaf. Exactly one long slender pointed leaf blade, gently curved, with a very short fine stalk. The leaf is black and grey Chinese brush ink with delicate translucent washes and dry brush texture. Leaf veins subtle. The single leaf lies diagonally from bottom left to top right, centered alone on entirely blank pure white paper. Simple elegant botanical subject. Empty unmarked background, no other objects, no branches or twigs.'
PROMPTS['D3']='Botanical watercolor illustration of one single willow LEAF: a narrow elongated lanceolate leaf blade with a pointed tip, a visible subtle central leaf vein and a tiny short petiole. Natural willow leaf anatomy, softly curving, six times as long as it is wide. Black and deep sage-grey Chinese ink washes, organic bleeding edges and delicate dry-brush texture, elegant hand-painted fine art. One leaf alone, centered diagonally on completely blank white paper, leaf blade fills most of composition. Pure empty background.'
key=sys.argv[1]
if len(sys.argv)>2 and sys.argv[2]=='result':
 event=json.loads((D/f'{key}-event.json').read_text())['event_id']
 url=BASE+'/gradio_api/call/infer/'+event
 with urllib.request.urlopen(url,timeout=40) as response:
  text=''
  while True:
   line=response.readline().decode();text+=line
   if not line:break
   if line.startswith('data:'):
    (D/f'{key}-result.sse').write_text(text)
    print(line.strip(),flush=True)
else:
 payload={'data':[PROMPTS[key],3591 if key=='D' else 9341,False,768,768,4]}
 (D/f'{key}-request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 req=urllib.request.Request(BASE+'/gradio_api/call/infer',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=20) as response:j=json.load(response)
 (D/f'{key}-event.json').write_text(json.dumps(j));print(key,j,flush=True)
