"""Enable a native selection controller in the fictional review home only.
Run after prepare_review.py and verify.py, before starting the review window.
Never run this against a person's actual Herdr home.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'.review-home'
for name in ('ink-spaces','ink-agents','ink-tabs','ink-pane'):
    p=HOME/'mods'/name/'fixture.js';s=p.read_text()
    if 'snapshotSpaces' in s:continue
    s='import { shared } from "herdr";\n'+s
    s=s.replace('export const spaces = () => [','const snapshotSpaces = () => [').replace('export const agents = () => [','const snapshotAgents = () => [')
    s+='\nexport const spaces=()=>snapshotSpaces().map(s=>({...s,active:s.id===(shared("ink.review.space")??"space-a")}));\nexport const agents=()=>snapshotAgents().map(a=>({...a,focused:a.address===(shared("ink.review.agent")??"demo-a")}));\n'
    p.write_text(s)
p=HOME/'mods/ink-demo/main.js';s=p.read_text()
if 'nextCommand' not in s:
    s=s.replace('import { theme } from "herdr";','import { theme, shared, setShared, nextCommand } from "herdr";')
    s=s.replace('export default class Demo extends View {','''export default class Demo extends View {
  init(_props,cx) {
    cx.spawn(async cx => {
      for (;;) {
        const command=await nextCommand();
        if(command==="toggle") {
          setShared("ink.review.space", shared("ink.review.space")==="space-b"?"space-a":"space-b");
          setShared("ink.review.agent", shared("ink.review.agent")==="demo-b"?"demo-a":"demo-b");
          cx.notify();
        }
      }
    });
  }''')
    s=s.replace('第二版：底色更明亮，笔触与竹简已更新。','水墨仙鹤：朝左飞入，收翅后单脚落定。')
    p.write_text(s)
print('Fictional native selection controller enabled')
