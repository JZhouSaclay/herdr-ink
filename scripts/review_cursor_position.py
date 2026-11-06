"""Native cursor position regression; synthetic transcript, no model requests."""
from pathlib import Path
import subprocess,json,shutil
R=Path(__file__).resolve().parents[1];D=R/'.pi-cursor-position-review';D.mkdir(exist_ok=True)
before=json.loads(subprocess.check_output(['herdr-app','status'],text=True));(D/'before.json').write_text(json.dumps(before))
(D/'footer.ts').write_text('''import {truncateToWidth} from "@earendil-works/pi-tui";
import {writeFileSync} from "node:fs";
export default function(pi){
 const cleanups=[];const frames=[];
 pi.on("session_shutdown",()=>{for(const f of cleanups)f();});
 pi.on("session_start",(_e,ctx)=>ctx.ui.setFooter((tui)=>{
  const terminal=tui.terminal;const original=terminal.write;
  const wrapped=function(data){
   if(data.endsWith("\\x1b[?2026l")&&tui.currentLayout){
    const marker=tui.extractCursorPosition([...tui.currentLayout.lines],terminal.rows);
    const moves=[...data.matchAll(/\\x1b\\[(\\d+);(\\d+)H/g)];const last=moves.at(-1);
    if(marker&&last){
     const actual=[Number(last[1]),Number(last[2])];
     const expected=[marker.row+1,Math.min(terminal.columns,marker.col)+1];
     frames.push({actual,expected,matches:actual.every((n,i)=>n===expected[i]),cursor_after_images:last.index>data.lastIndexOf("\\x1b_G"),hardware:tui.getShowHardwareCursor()});
     if(frames.length>100)frames.shift();
     writeFileSync("/Users/jiezhou/herdr-ink-study/cursor-position-proof.json",JSON.stringify({frames},null,2)+"\\n");
    }
   }
   return original.call(this,data);
  };
  terminal.write=wrapped;cleanups.push(()=>{if(terminal.write===wrapped)terminal.write=original;});
  return {invalidate(){},render(width){return [truncateToWidth("✦ 光标位置验收 · 🧠 high · ⚡ 42 tok/s · MCP 2/2",width)];}};
 }));
}
''')
(D/'settings.json').write_text(json.dumps({'theme':'light','tuiMode':'fullscreen','showHardwareCursor':False,'packages':[],'defaultProvider':'fixture','defaultModel':'fixture','extensions':['/Users/jiezhou/Desktop/公司其他/pi-extension/extensions/pretty-tui/index.ts',str(D/'footer.ts')]}))
for name in ['pretty-tui.json','models.json']:
 shutil.copyfile(R/'.pi-ink-review'/name,D/name)
fixture=D/'fixture.jsonl';shutil.copyfile(R/'.pi-ink-review/sessions/--tmp--/fixture-v18.jsonl',fixture)
args={'name':'光标位置验收','space':before['space'],'folder':'/tmp','argv':['env','PI_CODING_AGENT_DIR='+str(D),'pi','--session',str(fixture),'--no-skills','--no-prompt-templates']}
created=json.loads(subprocess.check_output(['herdr-app','do','tab.new',json.dumps(args,ensure_ascii=False)],text=True))
(D/'created.json').write_text(json.dumps(created));print(json.dumps(created))
