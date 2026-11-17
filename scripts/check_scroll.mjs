import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
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
const theme={foreground:'#303632',muted:'#7a8177',dim:'#62695f',border:'#d8d6cc',hover:'#eceade',canvas:'#fbfbf7',ansi1:'#a04437',ansi2:'#4e633f'};
const text='中文长行 '+ 'abcdefghijklmnopqrstuvwxyz'.repeat(12)+'\n第二行';
const later='第二个文件';
let options, editor, change, written=null;
const reads=[];
let writeImpl=async(p,value,expected)=>{written={p,value,expected};};
const host={View:class{},div:()=>el(),svg:()=>el('svg'),image:()=>el('image'),v_flex:()=>el(),h_flex:()=>el(),
 spaces:()=>[{active:true,id:'space',folder:'/fixture'}],panes:()=>[],focused:()=>({}),
 theme:()=>theme,settings:()=>({font_family:'Hede Ink Mono'}),window:()=>({platform:'macos'}),
 EditorState:{new:o=>{options=o;editor={on:(_name,fn)=>{change=fn;return editor;},value:()=>o.value,release(){}};return editor;}},
 Editor:{new:()=>el('editor')},TextView:{markdown:()=>el('textview')},
 readTextFile:p=>new Promise(resolve=>reads.push({p,resolve})),
 writeTextFile:(...args)=>writeImpl(...args),
 appHome:()=>root,exec:async()=>({code:0,stdout:'',stderr:''}),nextCommand:()=>new Promise(()=>{}),
 scrollPaper:(_v,_id,content)=>content,inkLine:()=>el('inkLine'),
 list:(_id,count,_key,render)=>{const n=el('list');for(let i=0;i<count;i++)n.nodes.push(render(i));return n;},
 Input:{new:()=>el('input')},Scrollbar:{vertical:()=>el('scrollbar')}};
function load(name){const src=fs.readFileSync(path.join(root,'mods',name,'main.js'),'utf8').replace(/^import .*?;\s*$/gm,'').replace('export default class','return class');return new (new Function(...Object.keys(host),src)(...Object.values(host)))();}
const settle=()=>new Promise(resolve=>setTimeout(resolve,0));
const cx={spawn:fn=>pending.push(fn(cx)),notify(){}};
const pending=[];

const files=load('ink-files');
files.context={key:JSON.stringify({cwd:'/fixture',on:null,space:'space'}),cwd:'/fixture',on:null};
files.root='/fixture';
files.show('demo.txt',cx);
assert.equal(reads.at(-1).p,'/fixture/demo.txt','Relative paths resolve against the open folder');
reads.at(-1).resolve(text);
await settle();
assert.equal(options.soft_wrap,true,'Soft wrapping stays on');
assert.equal(options.readonly,false,'Local files open editable');
assert.equal(options.value,text,'Soft wrapping must not alter the source text');
assert.equal(files.dirty,false,'A freshly read file is not dirty');

// 快速切换文件时，旧读取不得覆盖新选择
files.show('other.txt',cx);
assert.equal(files.file,'other.txt');
reads.at(-1).resolve(later);
await settle();
assert.equal(options.value,later,'Latest selection wins');

// 编辑后自动保存，并把读到的原文作为写入前提
options.value=`${later}\n新增`;
change();
assert.equal(files.dirty,true,'Typing marks the draft dirty');
files.changedAt=Date.now()-1000;
files.autosave(cx);
await settle();
assert.deepEqual(written,{p:'/fixture/other.txt',value:`${later}\n新增`,expected:later},'Autosave writes once with the original text as expected value');
assert.equal(files.dirty,false,'Successful save clears the dirty mark');

// 磁盘内容已变时写入失败，保留脏状态与提示
writeImpl=async()=>{throw new Error("Error: 'other.txt': file changed on disk");};
options.value=`${later}\n第二次编辑`;
change();
files.original='磁盘上的旧内容';
files.changedAt=Date.now()-1000;
files.autosave(cx);
await settle();
assert.equal(files.failed,true,'Refused save is reported');
assert.equal(files.dirty,true,'Refused save keeps the draft dirty');
assert.ok(files.notice.startsWith('Cannot save:'),'Refused save explains itself');

const changes=load('ink-changes');changes.setLines(['@@ -8,2 +8,2 @@',' same','-old','+'+'x'.repeat(200)]);
assert.deepEqual(changes.rows.map(r=>r.number),[undefined,8,9,9]);
const row=changes.diffRow(changes.rows[3],theme);
assert.equal(row.styles.h,undefined,'Wrapped diff row must not have a fixed height');
assert.equal(row.nodes[1].styles.truncate,undefined);assert.equal(row.nodes[1].styles.whitespace_normal.length,0);
assert.equal(row.nodes[1].styles.line_height,'20px');assert.equal(row.nodes[1].nodes[0],'x'.repeat(200));
assert.equal(changes.diffWidth,undefined,'No content-dependent horizontal minimum width');
console.log('PASS scroll / editable local files, unchanged source text, stale read protection, autosave expected value, refused write, diff line numbering and variable-height untruncated rows');