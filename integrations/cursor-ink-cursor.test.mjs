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
const {createInkCursor}=await loader.import(resolve(import.meta.dirname,'pretty-tui-v18-cursor/ink-cursor.ts'));
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
