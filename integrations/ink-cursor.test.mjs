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
const {createInkCursor}=await loader.import(resolve(import.meta.dirname,'./pretty-tui-v18-cursor/ink-cursor.ts'));
const {insertFrameImages}=await loader.import(resolve(import.meta.dirname,'./pretty-tui-v18-cursor/rounded-bubbles.ts'));
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
