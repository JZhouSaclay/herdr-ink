import fs from 'node:fs';
import assert from 'node:assert/strict';
const root='/Users/jiezhou/herdr-ink-study';
function el(kind='div') {
  const data={kind,styles:{},nodes:[]};let proxy;
  proxy=new Proxy(data,{get(o,k){
    if(k in o)return o[k];
    if(k==='child')return n=>(o.nodes.push(n),proxy);
    if(k==='children')return ns=>(o.nodes.push(...ns),proxy);
    if(k==='when')return (yes,fn)=>(yes?fn(proxy):proxy);
    return (...args)=>(o.styles[k]=args.length===1?args[0]:args,proxy);
  }});return proxy;
}
const theme={foreground:'#303632',dim:'#62695f',ansi1:'#a04437',ansi2:'#4e633f'};
const location={cwd:'/fixture',on:null,space:'space'};
const text='中文长行 '+ 'abcdefghijklmnopqrstuvwxyz'.repeat(12)+'\n第二行';
let options;const pending=[];
const host={View:class{},div:()=>el(),svg:()=>el('svg'),v_flex:()=>el(),h_flex:()=>el(),
 spaces:()=>[{active:true,id:'space',folder:'/fixture'}],panes:()=>[],focused:()=>({}),
 theme:()=>theme,settings:()=>({font_family:'Hede Ink Mono'}),window:()=>({platform:'macos'}),
 EditorState:{new:o=>(options=o,{release(){}})},Editor:{new:()=>el('editor')},
 readTextFile:async()=>text,scrollPaper:(_v,_id,content)=>content,inkLine:()=>el('inkLine'),
 list:(_id,count,_key,render)=>{const n=el('list');for(let i=0;i<count;i++)n.nodes.push(render(i));return n;},
 Input:{new:()=>el('input')},Scrollbar:{vertical:()=>el('scrollbar')}};
function load(name){const src=fs.readFileSync(`${root}/mods/${name}/main.js`,'utf8').replace(/^import .*?;\s*$/gm,'').replace('export default class','return class');return new (new Function(...Object.keys(host),src)(...Object.values(host)))();}
const cx={spawn:fn=>pending.push(fn(cx)),notify(){}};
const files=load('ink-files');files.context={key:JSON.stringify(location)};files.root='/fixture';
files.show('demo.txt',cx);await Promise.all(pending);
assert.equal(options.soft_wrap,true);assert.equal(options.readonly,true);assert.equal(options.value,text,'Soft wrapping must not alter the copied source');
files.file='other.txt';options=null;pending.length=0;files.show('demo.txt',cx);files.file='other.txt';await Promise.all(pending);assert.equal(options,null,'Stale read cannot replace the new selection');
const changes=load('ink-changes');changes.setLines(['@@ -8,2 +8,2 @@',' same','-old','+'+'x'.repeat(200)]);
assert.deepEqual(changes.rows.map(r=>r.number),[undefined,8,9,9]);
const row=changes.diffRow(changes.rows[3],theme);
assert.equal(row.styles.h,undefined,'Wrapped diff row must not have a fixed height');
assert.equal(row.nodes[1].styles.truncate,undefined);assert.equal(row.nodes[1].styles.whitespace_normal.length,0);
assert.equal(row.nodes[1].styles.line_height,'20px');assert.equal(row.nodes[1].nodes[0],'x'.repeat(200));
assert.equal(changes.diffWidth,undefined,'No content-dependent horizontal minimum width');
console.log('PASS scroll / readonly native soft wrap, unmodified source, stale read protection, diff line numbering and variable-height untruncated rows');
