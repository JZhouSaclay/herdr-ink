"""Prepare a separate Herdr home for native visual review, using fictional data.
No terminal is launched, no commands are sent to a real space, and the user's
Herdr home is never written. Actions in fixture modules are deliberately inert.
"""
from pathlib import Path
import json, shutil, re
ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'.review-home'
HOME.mkdir(exist_ok=True)
for name in ('mods','layouts','themes'):
    shutil.copytree(ROOT/name,HOME/name,dirs_exist_ok=True)
fixture='''
const tabs = [
  {id:"tab-a",name:"山水布局",named:true,active:true,status:"working"},
  {id:"tab-b",name:"素材整理",named:true,status:"done"},
  {id:"tab-c",name:"交互检查",named:true,status:"blocked"},
];
export const spaces = () => [
  {id:"space-a",name:"水墨书斋",named:true,active:true,machine:null,folder:"",tabs,status:"working"},
  {id:"space-b",name:"日常项目",named:true,machine:null,folder:"",tabs:[],status:"idle"},
  {id:"space-c",name:"随手记",named:true,machine:null,folder:"",tabs:[],status:"idle"},
];
export const agents = () => [
  {address:"demo-a",pane:"pane-a",tab:"tab-a",tab_name:"山水布局",space:"space-a",space_name:"水墨书斋",status:"working",focused:true,seq:3,program:{name:"Codex",agent:true}},
  {address:"demo-c",pane:"pane-c",tab:"tab-c",tab_name:"交互检查",space:"space-a",space_name:"水墨书斋",status:"blocked",seq:4,program:{name:"Claude Code",agent:true}},
  {address:"demo-b",pane:"pane-b",tab:"tab-b",tab_name:"素材整理",space:"space-a",space_name:"水墨书斋",status:"done",seq:2,program:{name:"Codex",agent:true}},
  {address:"demo-d",pane:"pane-d",tab:"tab-d",tab_name:"终端",space:"space-b",space_name:"日常项目",status:"idle",seq:1,program:{name:"Codex",agent:true}},
];
export const panes=()=>agents().map(a=>({...a,terminal:a.address,title:a.tab_name,cwd:"~/projects/ink-study"}));
export const terminals=()=>[];
export const focused=()=>({agent:"demo-a"});
export const machines=()=>[{name:null,layout:"ready"}];
export const exec=async()=>({exit_code:0,stdout:"",stderr:""});
export const hc=async()=>({exit_code:0,stdout:"[]",stderr:""});
export const watchFolder=()=>()=>{};
export const run=()=>{};
export const setAgentOrder=()=>{};
'''
replace_names={'spaces','agents','panes','terminals','focused','machines','exec','hc','watchFolder','run','setAgentOrder'}
for original in (ROOT/'mods').iterdir():
    folder=HOME/'mods'/original.name
    p=folder/'main.js'
    s=p.read_text()
    def rewrite(m):
        names=[n.strip() for n in m.group(1).split(',')]
        fake=[n for n in names if n in replace_names]
        real=[n for n in names if n not in replace_names]
        return ('import { '+', '.join(real)+' } from "herdr";\n' if real else '')+('import { '+', '.join(fake)+' } from "./fixture.js";' if fake else '')
    s=re.sub(r'import \{([^}]+)\} from "herdr";',rewrite,s)
    p.write_text(s)
    (folder/'fixture.js').write_text(fixture)

# Demo terminal is just a native mod containing safe fictional text. It is not a shell.
folder=HOME/'mods/ink-demo';folder.mkdir(exist_ok=True)
(folder/'mod.json').write_text('{"place":"none"}')
(folder/'main.js').write_text('''
import { View, div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme } from "herdr";
export default class Demo extends View {
  render() {
    const t=theme();
    const line=(text,color=t.foreground)=>div().h(30).text_color(color).child(text);
    return v_flex().size_full().bg("#fcfcf93d").p(24).gap(2).font_family("JetBrains Mono").text_size(14)
      .child(line("~/projects/ink-study  main",t.dim))
      .child(div().h(20))
      .child(line("❯  制作一套淡雅的水墨书斋布局",t.accent))
      .child(div().h(16))
      .child(line("第二版：底色更明亮，笔触与竹简已更新。"))
      .child(line("保留原有工作方式，让界面留出更多呼吸的空间。"))
      .child(div().h(16))
      .child(line("  ✓  水墨山水 · 中央工作区共用背景",t.done))
      .child(line("  ✓  墨痕目录 · 当前工作区与 Agent",t.done))
      .child(line("  ✓  竹简标签 · 墨环与状态印记",t.done))
      .child(div().h(24))
      .child(h_flex().gap(8).items_center().text_color(t.accent).child("❯").child(div().w(7).h(17).bg(t.accent)))
      .child(div().flex_1())
      .child(div().text_size(11).text_color(t.dim).child("原生界面预览 · 示例数据 · 未连接真实终端"));
  }
}
''')
layout=json.loads((HOME/'layouts/ink-study.json').read_text())
def walk(n):
    yield n
    for c in n.get('children',[]):yield from walk(c)
for n in walk(layout):
    if n['id']=='main':
        # Real pane header component is mounted above the demo terminal below.
        n.clear();n.update({'id':'main','type':'column','border':{'width':1,'color':'#879086'},'children':[
          {'id':'demo-header','type':'block','size':{'px':30},'content':{'mod':'ink-pane','props':{'pane':'pane-a'}}},
          {'id':'demo-body','type':'block','content':{'mod':'ink-demo'}}]})
    if n['id']=='status':n['content']={'mod':'ink-demo-status'}
folder=HOME/'mods/ink-demo-status';folder.mkdir(exist_ok=True)
(folder/'mod.json').write_text('{"place":"none"}')
(folder/'main.js').write_text('''import {View,div} from "gpui-kit"; import {theme} from "herdr"; export default class Status extends View {render(){return div().size_full().px(18).pt(6).text_size(11).text_color(theme().dim).bg(theme().chrome).child("此电脑     main     4 Agents");}}''')
(HOME/'layouts/ink-study.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2))
(HOME/'shared.json').write_text(json.dumps({'layout':'ink-study','frame.welcomed':True,'workspace.panels':['files','changes']}))
(HOME/'settings.json').write_text(json.dumps({'sounds':{'enabled':False},'telemetry':False,'appearance':'light'}))
# A stable physical-size preview, independent of the user's window geometry.
(HOME/'window.json').write_text(json.dumps({'state':'windowed','bounds':[100,100,1440,960]}))
(HOME/'update-notes.json').write_text(json.dumps({'last_run':'0.1.13','presented':['0.1.13']}))
print(HOME)
