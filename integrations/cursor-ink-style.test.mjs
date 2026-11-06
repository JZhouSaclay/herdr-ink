import assert from 'node:assert/strict';
import { test } from 'node:test';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { existsSync, realpathSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { inflateSync } from 'node:zlib';
let agent=dirname(realpathSync(execFileSync('which',['pi'],{encoding:'utf8'}).trim()));
while(!existsSync(join(agent,'package.json')))agent=dirname(agent);
const require=createRequire(join(agent,'package.json'));
const {createJiti}=require('jiti');
const loader=createJiti(import.meta.url,{moduleCache:false,alias:{
 '@earendil-works/pi-tui':require.resolve('@earendil-works/pi-tui'),
 '@earendil-works/pi-coding-agent':join(agent,'dist/index.js')
}});
const root=resolve(import.meta.dirname,'pretty-tui-v18-cursor');
const mod=await loader.import(join(root,'rounded-bubbles.ts'));
const palette=await loader.import(join(root,'user-bubble-background.ts'));
const {INK_FRAME_FLAG}=await loader.import(join(root,'ink-frame.ts'));
function pixels(png){
 let offset=8,parts=[],width,height;
 while(offset<png.length){let n=png.readUInt32BE(offset),type=png.toString('ascii',offset+4,offset+8),data=png.subarray(offset+8,offset+8+n);if(type==='IHDR'){width=data.readUInt32BE(0);height=data.readUInt32BE(4);}if(type==='IDAT')parts.push(data);offset+=n+12;}
 const raw=inflateSync(Buffer.concat(parts));return {width,height,raw,rgba(x,y){return [...raw.subarray(y*(width*4+1)+1+x*4,y*(width*4+1)+5+x*4)];}};
}
test('opt-in neutral paper palette preserves original light and dark settings',()=>{
 assert.equal(palette.userBubbleColor('light'),0xe8f3fe);
 assert.equal(palette.userBubbleColor('light',true),0xf1f3ee);
 assert.equal(palette.userBubbleColor('dark',true),0x303030);
 const p=pixels(mod.roundedSlicePng(100,60,0,60,palette.userBubbleColor('light',true)));
 assert.deepEqual(p.rgba(50,30),[241,243,238,255]);
 assert.match(palette.userBubbleBackground('text\x1b[0m尾','light',true),/241;243;238/);
});
test('editor frame is transparent inside with textured edges and slice-stable pixels',()=>{
 const cell={widthPx:10,heightPx:20,topGap:9};
 const whole=pixels(mod.roundedSlicePng(320,100,0,100,0x58695b|INK_FRAME_FLAG,cell));
 assert.deepEqual(whole.rgba(100,50),[88,105,91,0]);
 assert.equal(whole.rgba(40,10)[3],0,'working label has no stroke underneath');
 let values=new Set();for(let y=12;y<88;y++)values.add(whole.rgba(5,y)[3]);
 assert.ok(values.size>10,'edge visibly varies in density');
 assert.ok(whole.rgba(5,50)[3]>0);
 const slice=pixels(mod.roundedSlicePng(320,100,40,40,0x58695b|INK_FRAME_FLAG,cell));
 for(let y=0;y<40;y++)for(let x=0;x<320;x++)assert.deepEqual(slice.rgba(x,y),whole.rgba(x,y+40));
 assert.throws(()=>mod.roundedSlicePng(320,100,0,100,INK_FRAME_FLAG),/cell dimensions/);
});
test('frame markers merge only equivalent rows; coexist with original bubble markers and cache safely',()=>{
 const lines=[0,1,2].map(y=>'   '+mod.markInkFrameRow(4,y,3,22,0x58695b,6)+' '.repeat(22));
 const frame=mod.visibleBubbleSlices(lines,40)[0];assert.equal(frame.x,3);assert.equal(frame.rows,3);assert.equal(frame.topGap,6);
 assert.equal(mod.stripBubbleMarkers(lines[0]),' '.repeat(25));
 const painter=new mod.BubbleImagePainter();
 const first=painter.paint(lines,40,{widthPx:8,heightPx:16},false);assert.match(first,/a=t/);
 const again=painter.paint(lines,40,{widthPx:8,heightPx:16},false);assert.ok(!again.includes('a=t'));
 const changed=painter.paint(lines.map(s=>s.replace(',6\x07',',7\x07')),40,{widthPx:8,heightPx:16},false);assert.match(changed,/a=t/);
 const mixed=mod.visibleBubbleSlices([...lines,mod.markBubbleRow(1,0,1,10,0xe8f3fe)+'hello'],40);assert.equal(mixed.length,2);
 assert.equal(mixed[1].color,0xe8f3fe);assert.equal(mixed[1].topGap,undefined);
});
test('complete extension imports with installed Pi loader',async()=>{
 const extension=await loader.import(join(root,'index.ts'));assert.equal(typeof extension.default,'function');
});

test('editor preserves width, mouse origin and native cursor marker; teardown restores prototypes',async()=>{
 const agentMod=await loader.import(join(agent,'dist/index.js'));
 const tui=await loader.import(require.resolve('@earendil-works/pi-tui'));
 const extension=await loader.import(join(root,'index.ts'));
 const proto=agentMod.CustomEditor.prototype;
 const original=proto.render,mouse=proto.handleMouse;
 let tornDown=false;
 proto.render=function(width){this.lastNativeWidth=width;this.renderedVisibleLineCount=1;return ['─'.repeat(width),'\x1b_pi:c\x07中'+ ' '.repeat(width-2),'─'.repeat(width)];};
 proto.handleMouse=function(event){this.nativeMouse=event;};
 const hooks=new Map();
 const api=new Proxy({on(name,fn){if(!hooks.has(name))hooks.set(name,[]);hooks.get(name).push(fn);}},{get(target,key){return target[key]??(()=>{});}});
 try {
   extension.default(api);
   const editor={borderColor:x=>x};
   const lines=proto.render.call(editor,80);
   assert.equal(editor.lastNativeWidth,78);
   for(const line of lines)assert.equal(tui.visibleWidth(line),80);
   assert.ok(lines[1].includes('\x1b_pi:c\x07'),'native cursor marker retained');
   proto.handleMouse.call(editor,{x:4,y:1,width:80});assert.equal(editor.nativeMouse.x,3);assert.equal(editor.nativeMouse.width,78);
   for(const fn of hooks.get('session_shutdown')??[])await fn({},{});
   tornDown=true;
   assert.notEqual(proto.render,original,'restored our fake original render, not an unrelated prototype');
   assert.equal(proto.render.call({borderColor:x=>x},80)[0].length,80);
 } finally {
   if(!tornDown)for(const fn of hooks.get('session_shutdown')??[])await fn({},{});
   proto.render=original;proto.handleMouse=mouse;
 }
});


test('ink bubble has dark textured outline, paper interior, transparent corners and slice-stable edges',()=>{
 const color=0xf1f3ee|mod.INK_BUBBLE_FLAG;
 const whole=pixels(mod.roundedSlicePng(180,100,0,100,color));
 assert.deepEqual(whole.rgba(90,50),[241,243,238,255]);
 assert.equal(whole.rgba(0,0)[3],0);
 assert.ok(whole.rgba(90,0)[0]<115,'top outline is dense ink');
 assert.ok(whole.rgba(0,50)[0]<115,'side outline is dense ink');
 const slice=pixels(mod.roundedSlicePng(180,100,40,30,color));
 for(let y=0;y<30;y++)for(let x=0;x<180;x++)assert.deepEqual(slice.rgba(x,y),whole.rgba(x,y+40));
});

test('background and footer drawing share one cursor save slot, preserving native cursor and IME anchor',async()=>{
 const footer=await loader.import(join(root,'ink-footer.ts'));
 const painter=new mod.BubbleImagePainter();
 const lines=[mod.markInkFrameRow(8,0,1,20,0x58695b)+' '.repeat(20),footer.inkFooterLine('✦ model · 🧠 high · ⚡ 42 tok/s')];
 const output=painter.paint(lines,80,{widthPx:8,heightPx:20},false);
 assert.equal(output.split('\x1b7').length-1,1,'DEC save has only one slot');
 assert.equal(output.split('\x1b8').length-1,1,'restore exactly the original hardware cursor');
 assert.equal((output.match(/a=p,/g)??[]).length,4,'frame and all three icons still paint');
});
