// Exercise real render/event code with a minimal host. Native checks are separate.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const fixture=await import(path.join(root,'.review-home/mods/ink-tabs/fixture.js'));
const theme=JSON.parse(fs.readFileSync(path.join(root,'themes/ink-study.json'))).colors;
let commands=[];
globalThis.localStorage={getItem:()=>null,setItem:()=>{},removeItem:()=>{}};
function element(kind,arg) {
  const n={kind,arg,nodes:[],styles:{},events:{}};
  const proxy=new Proxy(n,{get(target,key){
    if(key in target)return target[key];
    if(key==='when')return (on,fn)=>on?fn(proxy):proxy;
    if(key==='child')return child=>{if(child!=null)n.nodes.push(child);return proxy;};
    if(key==='children')return children=>{n.nodes.push(...children);return proxy;};
    if(String(key).startsWith('on_'))return (...args)=>{n.events[key]=args.at(-1);return proxy;};
    if(key==='transition')return (property,policy)=>{n.transitions??={};n.transitions[property]=policy;return proxy;};
    if(key==='hover')return fn=>{n.hoverStyle=fn;return proxy;};
    return (...args)=>{n.styles[key]=args.length<=1?args[0]:args;return proxy;};
  }});
  return proxy;
}
const timers=[];let notifications=0;
const cx={notify(){notifications++;},stop_propagation(){},spawn(){},timer:{every(){},after(ms,callback){
  const task={ms,callback,cancelled:false,done:false,cancel(){this.cancelled=true;},is_done(){return this.done;}};
  timers.push(task);return task;
}}};
const tree=JSON.parse(fs.readFileSync(path.join(root,'layouts/ink-study.json')));
const sharedState = new Map();
const host={...fixture,View:class {},div:()=>element('div'),svg:p=>element('svg',p),image:p=>element('image',p),h_flex:()=>element('h_flex'),v_flex:()=>element('v_flex'),theme:()=>theme,layout:()=>tree,shared:key=>sharedState.get(key)??null,setShared:(key,value)=>sharedState.set(key,value),props:()=>({}),window:()=>({platform:'macos',titlebar:'none',fullscreen:false}),settings:()=>({zoom:1}),run:(name,args)=>commands.push({name,args}),openOverlay(){},closeOverlay(){},updates:()=>({app:{}})};
const objectsSource=fs.readFileSync(path.join(root,'scripts/space-objects.js'),'utf8').replace(/^import .*?;\s*$/gm,'').replaceAll('export function ','function ');
Object.assign(host,new Function('image','shared','setShared',objectsSource+'\nreturn {spaceObjects,spaceObject};')(host.image,host.shared,host.setShared));
const craneSource=fs.readFileSync(path.join(root,'scripts/crane-motion.js'),'utf8').replace(/^import .*?;\s*$/gm,'').replace('export class CraneMotion','return class CraneMotion');
host.CraneMotion=new Function('div','image',craneSource)(host.div,host.image);
const pathBuilder=()=>new Proxy({},{get(_t,k){if(k==='build')return ()=>({});return ()=>pathBuilder();}});
const inkSource=fs.readFileSync(path.join(root,'scripts/ink-style.js'),'utf8').replace(/^import .*?;\s*$/gm,'').replaceAll('export function ','function ');
const inkKit=new Function('div','svg','PathBuilder','window',inkSource+'\nreturn {inkLine,inkStamp};')(host.div,host.svg,{fill:pathBuilder},{paint_path:()=>element('paint_path')});
Object.assign(host,inkKit);
function load(name){
  let s=fs.readFileSync(path.join(root,'mods',name,'main.js'),'utf8');
  s=s.replace(/^import .*?;\s*$/gm,'').replace(/^export function /gm,'function ').replace('export default class','return class');
  const Class=new Function(...Object.keys(host),s)(...Object.values(host));
  const instance=new Class();instance.init?.({},cx);return instance;
}
function find(n,predicate){if(!n||typeof n!=='object')return null;if(predicate(n))return n;for(const c of n.nodes??[]){const f=find(c,predicate);if(f)return f;}return null;}
const row=(tree,id)=>{const n=find(tree,n=>n.styles?.id===id);assert.ok(n,id);return n;};
const frameOpacity=n=>{const a=find(n,n=>n.kind==='image'&&n.arg.endsWith('row-frame-v4.png'));assert.ok(a,'ink frame');return a.styles.opacity;};
const strokePath=n=>find(n,n=>n.kind==='image'&&/stroke(-alt)?-v3\.png$/.test(n.arg))?.arg;
const opacity=n=>{const a=find(n,n=>n.kind==='image'&&/stroke(-alt)?-v3\.png$/.test(n.arg));assert.ok(a,'stroke');return a.styles.opacity;};
for(const [name,id,selected] of [['ink-spaces','space-space-b','space-space-a'],['ink-agents','ag-demo-b','ag-demo-a']]){
  const instance=load(name);let tree=instance.render(cx);
  assert.equal(opacity(row(tree,id)),.085,'default stroke is slightly deeper');
  assert.ok(strokePath(row(tree,id)).endsWith('stroke-alt-v3.png'),'unselected rows use second ink shape');
  assert.ok(strokePath(row(tree,selected)).endsWith('stroke-v3.png'),'selected rows use first ink shape');
  assert.equal(frameOpacity(row(tree,id)),0,'default frame hidden');
  assert.equal(opacity(row(tree,selected)),.085,'selected name stays on the same pale ink');
  assert.equal(frameOpacity(row(tree,selected)),.74,'selected frame visible');
  row(tree,id).events.on_hover(true,cx);tree=instance.render(cx);
  assert.equal(opacity(row(tree,id)),.085,'hover never darkens the name area');
  assert.equal(frameOpacity(row(tree,id)),.36,'hover reveals a light frame');
  assert.ok(strokePath(row(tree,id)).endsWith('stroke-alt-v3.png'),'hover does not change ink shape');
  row(tree,id).events.on_hover(false,cx);tree=instance.render(cx);
  assert.equal(opacity(row(tree,id)),.085,'exit preserves pale stroke');
  assert.equal(frameOpacity(row(tree,id)),0,'exit hides frame');
  if(name==='ink-agents'){
    assert.equal(find(tree,n=>/^sec-/.test(n.styles?.id??'')),null,'no priority section headings');
    const working=row(tree,'ag-demo-a');
    assert.ok(find(working,n=>n.kind==='svg'&&n.arg.endsWith('ink-ring-v9.svg')&&n.styles.spin===1600),'ink arc rotates');
  }
  console.log('PASS real render events / '+name+' / selection-based ink shape, slightly deeper ink, hover frame, exit, selected frame');
}
const tabs=load('ink-tabs');let rendered=tabs.render(cx);
assert.equal(row(rendered,'tab-tab-a').styles.px,12,'compact tab padding');
assert.equal(row(rendered,'tab-tab-a').styles.gap,8,'clear title/action spacing');
assert.ok(find(row(rendered,'tab-tab-b'),n=>n.kind==='image'&&/bamboo-v17-\d+\.png$/.test(n.arg)),'inactive tab has bamboo too');
row(rendered,'close-tab-b').events.on_click({},cx);
assert.equal(commands.at(-1).name,'tab.select','hidden close region selects instead of closing');
row(rendered,'tab-tab-b').events.on_hover(true,cx);rendered=tabs.render(cx);
row(rendered,'close-tab-b').events.on_click({},cx);
assert.equal(commands.at(-1).name,'tab.close','visible close closes');
assert.equal(row(rendered,'tab-tab-a').styles.h,40);
assert.ok(row(rendered,'tab-tab-a').styles.w>=136);
const titleNode=find(row(rendered,'tab-tab-a'),n=>n.styles?.font_family==='LXGW WenKai Mono');
assert.ok(titleNode,'title uses Songti');
assert.equal(titleNode.styles.min_w,0,'long labels truncate without moving actions');
assert.ok(Object.hasOwn(titleNode.styles,'flex_1'),'title fills available width');
assert.ok(Object.hasOwn(row(rendered,'tab-actions-tab-a').styles,'flex_none'),'actions do not shrink');
assert.ok(row(rendered,'tab-tab-a').nodes.at(-1).styles.id==='tab-actions-tab-a','actions occupy the trailing slot');
assert.equal(row(rendered,'tab-status-tab-a').styles.size,16,'status slot keeps a fixed width');
assert.ok(find(row(rendered,'tab-tab-a'),n=>n.kind==='image'&&n.arg.endsWith('ink-number-v11-1.png')),'brush numeral restored');
const idleCard=row(load('ink-agents').render(cx),'ag-demo-d');
assert.ok(find(idleCard,n=>n.kind==='svg'&&n.arg.endsWith('ink-seal-v9.svg')),'idle uses a brush seal');
assert.ok(find(idleCard,n=>n.nodes?.includes('闲')),'idle clearly says 闲');
console.log('PASS real render events / ink-tabs / taller proportioned bamboo, hover, safe close; idle ink seal');

// Fresh playback nodes, finite native GIF phase, cancellation, and no hover replay.
for(const name of ['ink-spaces','ink-agents']) {
  let selected=name==='ink-spaces'?'space-a':'demo-a';
  if(name==='ink-spaces')host.spaces=()=>fixture.spaces().map(s=>({...s,active:s.id===selected}));
  else host.agents=()=>fixture.agents().map(a=>({...a,focused:a.address===selected}));
  const instance=load(name);
  const options=name==='ink-spaces'?['space-a','space-b']:['demo-a','demo-b'];
  const kind=name==='ink-spaces'?'space':'agent';
  const slot=(rendered,id)=>find(rendered,n=>String(n.styles?.id??'').startsWith(`crane-slot-${kind}-${id}-`));
  const bird=n=>find(n,n=>n.kind==='image'&&/crane-(arrival|rest)/.test(n.arg));
  let rendered=instance.render(cx);
  assert.ok(bird(slot(rendered,selected)).arg.endsWith('crane-rest-ink-left-v8.png'),'initial selection holds flight pose 06');
  let previousTask=null;const instanceIds=[];
  for(const target of [options[1],options[0],options[1],options[0]]) {
    selected=target;rendered=instance.render(cx);
    const n=slot(rendered,target);assert.ok(n,'selected corner exists');
    assert.equal(n.styles.w,36,'wing clearance');
    assert.equal(n.nodes.length,1,'single playback instance');
    const armed=bird(n);instanceIds.push(armed.styles.id);
    assert.ok(armed.arg.endsWith('crane-arrival-ink-left-v8.gif'),'left-facing wing animation armed');
    assert.equal(armed.styles.opacity,0,'first paint is ready for fade-in');
    assert.equal(armed.styles.left,14,'arrival starts on the right');
    const before=timers.length;
    n.events.on_size_change({width:36,height:34},cx);
    n.events.on_size_change({width:36,height:34},cx);
    assert.equal(timers.length,before+1,'one phase deadline, no per-frame timer');
    const current=timers.at(-1);assert.equal(current.ms,2000);
    if(previousTask){
      assert.equal(previousTask.cancelled,true,'old playback cancelled');
      const beforeNotify=notifications;
      previousTask.callback(cx);
      assert.equal(notifications,beforeNotify,'stale callback cannot change a new arrival');
      assert.equal(instance.craneMotion.phase,'playing');
    }
    rendered=instance.render(cx);
    const playing=bird(slot(rendered,target));
    assert.equal(playing.styles.opacity,.88);assert.equal(playing.styles.left,0);
    assert.equal(playing.transitions.left.duration,1600);
    assert.ok(!slot(rendered,options.find(id=>id!==target)),'old ornament removed immediately');
    const parent=row(rendered,name==='ink-spaces'?`space-${target}`:`ag-${target}`);
    assert.ok(parent.styles.pr>=n.styles.w+n.styles.right,'text and status avoid wings');
    assert.equal(opacity(parent),.085);
    assert.ok(strokePath(parent).endsWith('stroke-v3.png'),'new selection switches to first ink shape');
    const other=row(rendered,name==='ink-spaces'?`space-${options.find(id=>id!==target)}`:`ag-${options.find(id=>id!==target)}`);
    assert.ok(strokePath(other).endsWith('stroke-alt-v3.png'),'previous selection restores second ink shape');
    previousTask=current;
  }
  assert.equal(new Set(instanceIds).size,instanceIds.length,'reselection creates a fresh GIF element identity');
  previousTask.done=true;previousTask.callback(cx);rendered=instance.render(cx);
  const resting=bird(slot(rendered,selected));
  assert.ok(resting.arg.endsWith('crane-rest-ink-left-v8.png'),'switches to static pose at deadline');
  const count=timers.length;
  slot(rendered,selected).events.on_size_change({width:36,height:34},cx);
  assert.equal(timers.length,count,'layout and hover never restart a settled crane');
  selected=options[1];rendered=instance.render(cx);slot(rendered,selected).events.on_size_change({width:36,height:34},cx);
  const ending=timers.at(-1);instance.close();assert.equal(ending.cancelled,true,'closing view cancels playback');
  const beforeNotify=notifications;ending.callback(cx);assert.equal(notifications,beforeNotify,'closed playback cannot notify');
  host.spaces=fixture.spaces;host.agents=fixture.agents;
  console.log('PASS crane sequence / '+name+' / left-facing GIF, 2000ms stop at flight pose 06, reselection, stale cancellation, text clearance');
}

// Check the compact session rows using the same host and render implementation.
{
  const original = {spaces:host.spaces,agents:host.agents,terminals:host.terminals,layout:host.layout};
  const longName = '这是一个很长很长但不应该挤占会话标题的工作区名称';
  let workspaces = [{id:'objects-a',name:longName,tabs:[{id:'objects-tab',name:'1',named:false}]},{id:'objects-b',name:'另一个工作区',tabs:[]}];
  host.spaces = () => workspaces;
  const assignments = host.spaceObjects(workspaces);
  assert.notEqual(assignments['objects-a'],assignments['objects-b'],'live spaces get different objects');
  workspaces = [...workspaces].reverse().map(s=>({...s,name:s.name+'改名'}));
  assert.deepEqual(host.spaceObjects(workspaces),assignments,'reorder and rename preserve space objects');
  host.agents = () => [{address:'test-pi',pane:'test-pane',space:'objects-a',space_name:longName,tab:'objects-tab',tab_index:1,title:'π - 会话名称包含 Pi 和 Codex 字样',status:'working',focused:true,seq:1,program:{name:'Pi',key:'pi'}}];
  host.terminals = () => [{address:'test-pi',labels:{}}];
  const text = n => typeof n==='string' ? n : (n?.nodes??[]).map(text).join(' ');
  const art = n => find(n,n=>n.kind==='image'&&n.arg.includes('object-v16-'));
  let view=load('ink-agents');let rendered=view.render(cx);let card=row(rendered,'ag-test-pi');
  assert.ok(text(card).includes('会话名称包含 Pi 和 Codex 字样'),'only leading program name is removed');
  assert.ok(!text(card).includes(longName),'space name does not consume card text');
  assert.ok(!text(card).includes('π -'),'Pi prefix removed');
  assert.ok(!find(card,n=>n.styles?.text_size===11),'no age label');
  assert.equal(art(card).styles.w,24,'fixed object width');
  const fullArt=art(card).arg;
  host.terminals = () => [{address:'test-pi',labels:{'pi.session_name':'真实会话名'}}];
  view=load('ink-agents');
  assert.ok(text(row(view.render(cx),'ag-test-pi')).includes('真实会话名'),'session metadata wins over terminal title');
  sharedState.set('agents.sort','grouped');
  assert.equal(art(row(view.render(cx),'ag-test-pi')).arg,fullArt,'grouped view uses the same object');
  sharedState.delete('agents.sort');
  host.layout=()=>({id:'sidebar',size:{px:76}});
  view=load('ink-agents');
  assert.equal(art(row(view.render(cx),'ag-test-pi')).arg,fullArt,'narrow sidebar uses the same object');
  Object.assign(host,original);
  console.log('PASS sidebar objects / stable across rename, reorder and grouping; fixed width; Pi prefix and age removed; real session metadata; narrow rail');
}
