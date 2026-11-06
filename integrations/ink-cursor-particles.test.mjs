import assert from 'node:assert/strict';
import {test} from 'node:test';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {existsSync,realpathSync} from 'node:fs';
import {dirname,join,resolve} from 'node:path';
let agent=dirname(realpathSync(execFileSync('which',['pi'],{encoding:'utf8'}).trim()));
while(!existsSync(join(agent,'package.json')))agent=dirname(agent);
const require=createRequire(join(agent,'package.json'));
const {createJiti}=require('jiti');
const loader=createJiti(import.meta.url,{moduleCache:false,alias:{'@earendil-works/pi-tui':require.resolve('@earendil-works/pi-tui')}});
const {createInkCursor}=await loader.import(resolve(import.meta.dirname,'./pretty-tui-cursor-particles/ink-cursor.ts'));
const {insertFrameImages,installRoundedBubbles}=await loader.import(resolve(import.meta.dirname,'./pretty-tui-cursor-particles/rounded-bubbles.ts'));
const {CURSOR_FRAME_COUNT,CURSOR_FRAME_MS,InkCursorImagePainter,nativeFrameCursor}=await loader.import(resolve(import.meta.dirname,'./pretty-tui-cursor-particles/ink-cursor-images.ts'));
const tui=await loader.import(require.resolve('@earendil-works/pi-tui'));
function fake(previous=false){const writes=[];let hardware=previous;return {writes,getShowHardwareCursor(){return hardware;},setShowHardwareCursor(value){hardware=value;},terminal:{write(value){writes.push(value);}}};}

test('steady ink bar uses hardware cursor and writes only once for repeated layout passes',()=>{
 const host=fake();const cursor=createInkCursor(()=>'bar');
 cursor.attach(host);assert.equal(host.getShowHardwareCursor(),true);
 assert.match(host.writes[0],/\x1b\[6 q/);assert.match(host.writes[0],/#58695b/);
 cursor.attach(host);assert.equal(host.writes.length,1);
 cursor.dispose();assert.equal(host.getShowHardwareCursor(),false);assert.match(host.writes[1],/\x1b\[0 q/);
 cursor.dispose();assert.equal(host.writes.length,2);
});
test('style changes, opt-out and teardown preserve the previous hardware-cursor preference',()=>{
 const host=fake(true);let style='underline';const cursor=createInkCursor(()=>style);
 cursor.attach(host);assert.match(host.writes.at(-1),/\x1b\[4 q/);
 style='block';cursor.attach(host);assert.match(host.writes.at(-1),/\x1b\[2 q/);
 style='default';cursor.attach(host);assert.equal(host.getShowHardwareCursor(),true);
 const count=host.writes.length;cursor.dispose();assert.equal(host.writes.length,count);
 cursor.attach(undefined);cursor.attach({terminal:{write(){throw Error('must not be called');}}});
});
test('real Pi cursor resolution removes inverse video while preserving text, columns and IME marker',()=>{
 for(const text of [' ','中','A']){
  const marked=tui.CURSOR_MARKER+tui.renderFakeCursor(text);
  const resolved=tui.TuiAltScreen.prototype.resolveFakeCursors.call({showHardwareCursor:true},[marked])[0];
  assert.equal(resolved,tui.CURSOR_MARKER+text);
  assert.equal(tui.visibleWidth(resolved),tui.visibleWidth(text));
  const old=tui.TuiAltScreen.prototype.resolveFakeCursors.call({showHardwareCursor:false},[marked])[0];
  assert.ok(old.includes('\x1b[7m'));
 }
});

test('frame images cannot override final native text/IME cursor, including unchanged text rows',()=>{
 const begin='\x1b[?2026h',end='\x1b[?2026l';
 // Mimic two image layers sharing DEC's one saved cursor slot.
 const images='\x1b7\x1b[40;10H\x1b7\x1b[43;20H\x1b8\x1b8';
 function finalPosition(data){
  let position=[1,1],saved=position;
  for(const token of data.matchAll(/\x1b\[(\d+);(\d+)H|\x1b([78])/g)){
   if(token[1])position=[Number(token[1]),Number(token[2])];
   else if(token[3]==='7')saved=position;else position=saved;
  }
  return position;
 }
 for(const position of [[41,12],[41,15],[41,13],[42,12]]){
  const nativeTail=`\x1b[${position[0]};${position[1]}H\x1b[?25h${end}`;
  const original=begin+nativeTail; // no changed text: just the cursor moves
  const broken=original.slice(0,-end.length)+images+end;
  assert.notDeepEqual(finalPosition(broken),position,'reproduce saved-slot cursor displacement');
  const fixed=insertFrameImages(original,images);
  assert.deepEqual(finalPosition(fixed),position);
  assert.ok(fixed.endsWith(nativeTail),'native caret and visibility must follow all images');
  assert.equal(fixed.split(end).length,2,'one synchronized frame');
 }
 const hidden=begin+'\x1b[?25l'+end;
 assert.ok(insertFrameImages(hidden,images).endsWith('\x1b[?25l'+end));
 assert.equal(insertFrameImages(hidden,''),hidden);
});

test('leaf particles span one Chinese glyph and keep looping on status redraws',()=>{
 let now=0;const painter=new InkCursorImagePainter(()=>now);
 const target={row:12,col:23};
 const native='\x1b[?2026h\x1b[12;23H\x1b[?25h\x1b[?2026l';
 assert.deepEqual(nativeFrameCursor(native),target);
 assert.equal(nativeFrameCursor(native.replace('?25h','?25l')),undefined);
 const first=painter.paint(target,'leaf');
 assert.ok(first.includes('c=2,r=1,z=2,C=1'));
 assert.ok(first.includes('\x1b[12;23H'));assert.ok(first.includes('a=t'));
 assert.equal(painter.animated,true);
 now=400;const second=painter.tick();assert.ok(second.includes('a=d,d=i'));assert.notEqual(second,first);
 now=2600;painter.paint(target,'leaf');assert.equal(painter.animated,true,'particle playback keeps looping after a full cycle');
 now=600000;painter.tick();assert.equal(painter.animated,true,'continuous playback after ten minutes');
 painter.paint({row:13,col:4},'leaf');assert.equal(painter.animated,true);
 const fixed=insertFrameImages(native,first,true);
 assert.ok(fixed.endsWith('\x1b[12;23H\x1b[?25l\x1b[?2026l'),'retain IME position while hiding hardware bar');
 painter.paint(target,'leaf-still');assert.equal(painter.animated,false);
 painter.paint(target,'ink');assert.equal(painter.animated,false);
 assert.ok(painter.paint(undefined,'leaf').includes('a=d'));assert.equal(painter.visible,false);
 assert.ok(painter.dispose().includes('a=d,d=I'));assert.equal(painter.dispose(),'');
});

test('wider leaf cursor fits the right edge without moving its text anchor',()=>{
 let now=0;const painter=new InkCursorImagePainter(()=>now);
 assert.ok(painter.paint({row:8,col:79},'leaf',false,80).includes('c=2,r=1'));
 const edge=painter.paint({row:8,col:80},'leaf',false,80);
 assert.ok(edge.includes('c=1,r=1'));assert.ok(edge.includes('\x1b[8;80H'));
 now=200;assert.ok(painter.tick().includes('c=1,r=1'),'animated frames retain viewport bounds');
 assert.ok(painter.paint({row:8,col:40},'ink',false,80).includes('c=1,r=1'),'ink stroke keeps original width');
 painter.dispose();
});

test('full breeze loop reuses bounded image assets and does not restart when caret moves',()=>{
 let now=0;const painter=new InkCursorImagePainter(()=>now);const ids=new Set();
 const placement=output=>Number(/a=p,i=(\d+)/.exec(output)[1]);
 let last;
 for(let i=0;i<CURSOR_FRAME_COUNT;i++){
  now=i*CURSOR_FRAME_MS;last=placement(painter.paint({row:8,col:30},'leaf'));ids.add(last);
 }
 assert.equal(ids.size,CURSOR_FRAME_COUNT,'all generated frames are reachable');
 const next=painter.paint({row:9,col:4},'leaf');
 assert.equal(placement(next),last,'moving caret keeps the current animation frame');
 now=CURSOR_FRAME_COUNT*CURSOR_FRAME_MS;
 const wrapped=painter.tick();
 assert.equal(placement(wrapped),[...ids][0],'the loop closes on its first frame');
 assert.ok(!wrapped.includes('a=t'),'next cycle reuses the uploaded first frame');
 painter.dispose();
});

test('cursor image reset reuploads its assets and fallback removes its placement',()=>{
 const painter=new InkCursorImagePainter(()=>0);const position={row:1,col:2};
 assert.ok(painter.paint(position,'leaf').includes('a=t'));
 assert.ok(!painter.paint(position,'leaf').includes('a=t'));
 assert.ok(painter.paint(position,'leaf',true).includes('a=t'));
 assert.ok(painter.paint(position,'bar').includes('a=d'));assert.equal(painter.visible,false);
});

test('animation updates only its overlay and stops permanently when the TUI stops',async()=>{
 const caps=tui.getCapabilities(),env=process.env.HERDR_ENV;process.env.HERDR_ENV='1';
 tui.setCapabilities({...caps,images:'kitty'});
 const writes=[];let renders=0;
 const proto={doRender(){renders++;this.terminal.write('\x1b[?2026h\x1b[12;23H\x1b[?25h\x1b[?2026l');},stop(){this.stopped=true;}};
 const host=Object.assign(Object.create(proto),{altScreenActive:true,stopped:false,previousScreen:[],terminal:{columns:80,rows:25,write(data){writes.push(data);}}});
 const errors=[];const installed=installRoundedBubbles(proto,error=>errors.push(error),()=> 'leaf');
 try{
  assert.equal(installed.available(),true);host.doRender();
  await new Promise(resolve=>setTimeout(resolve,150));
  assert.equal(renders,1,'animation must not rerender the transcript');
  assert.ok(writes.length>=2,'animated overlay emits another frame');
  assert.ok(writes.every(frame=>frame.endsWith('\x1b[12;23H\x1b[?25l\x1b[?2026l')));
  host.stop();const count=writes.length;
  await new Promise(resolve=>setTimeout(resolve,150));assert.equal(writes.length,count,'no output after stop');
  assert.deepEqual(errors,[]);
 }finally{installed.dispose();tui.setCapabilities(caps);if(env===undefined)delete process.env.HERDR_ENV;else process.env.HERDR_ENV=env;}
});

test('cached style must re-enable hardware cursor after Pi reload reapplies false',()=>{
 const host=fake();const cursor=createInkCursor(()=>'bar');
 cursor.attach(host);host.setShowHardwareCursor(false);
 const marked=tui.CURSOR_MARKER+tui.renderFakeCursor('中');
 assert.ok(tui.TuiAltScreen.prototype.resolveFakeCursors.call({showHardwareCursor:host.getShowHardwareCursor()},[marked])[0].includes('\x1b[7m'));
 cursor.attach(host);
 assert.equal(host.getShowHardwareCursor(),true);
 assert.equal(host.writes.length,2,'restore shape and color after the runtime-settings override');
 assert.equal(tui.TuiAltScreen.prototype.resolveFakeCursors.call({showHardwareCursor:host.getShowHardwareCursor()},[marked])[0],tui.CURSOR_MARKER+'中');
 cursor.dispose();assert.equal(host.getShowHardwareCursor(),false,'original preference is still restored');
});
