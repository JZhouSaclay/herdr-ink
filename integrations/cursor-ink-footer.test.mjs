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
const mod=await loader.import(resolve(import.meta.dirname,'pretty-tui-v18-cursor/ink-footer.ts'));
const tui=await loader.import(require.resolve('@earendil-works/pi-tui'));

test('footer artwork preserves columns, ANSI status colors and all data, including VS16',()=>{
 for(const text of ['✦ 模型 · 🧠 high · ⚡ 42 tok/s','⚡️ 20 tok/s','\x1b[35m🧠 high\x1b[0m · MCP 2/2 · 微信未连接']){
   const line=mod.inkFooterLine(text);
   assert.equal(tui.visibleWidth(line),tui.visibleWidth(text));
   assert.equal(mod.stripFooterMarkers(line),text.replace(/✦|🧠|⚡\uFE0F?/gu,s=>' '.repeat(tui.visibleWidth(s))));
   assert.equal(mod.inkFooterLine(line),line,'no duplicated markers on repeated rendering');
 }
});
test('three icons share one line, retain exact columns, upload once, reset, hide and dispose',()=>{
 const painter=new mod.FooterImagePainter();
 const lines=[mod.inkFooterLine('   ✦ model · 🧠 high · ⚡ 42 tok/s')];
 const first=painter.paint(lines,80,false,false);
 assert.equal((first.match(/a=p,/g)??[]).length,3);
 assert.ok(first.includes('\x1b[1;4H'),'model placement follows three leading spaces');
 assert.equal((first.match(/a=t,/g)??[]).length,3);
 const second=painter.paint(lines,80,false,false);
 assert.ok(!second.includes('a=t,'));
 assert.equal((second.match(/a=d,d=i/g)??[]).length,3);
 const reset=painter.paint(lines,80,true,false);assert.equal((reset.match(/a=t,/g)??[]).length,3);
 const hidden=painter.paint(lines,80,false,true);assert.ok(!hidden.includes('a=p,'));
 assert.equal((hidden.match(/a=d,d=I/g)??[]).length,3);
 assert.equal(painter.dispose(),'');
 const clipped=new mod.FooterImagePainter().paint([mod.inkFooterLine('  🧠')],3,false,false);
 assert.ok(!clipped.includes('a=p,'),'do not paint a truncated wide icon');
});
test('only attached footer output changes; opt-out and teardown restore the original method',()=>{
 let enabled=false;
 const original=function(){return ['🧠 high'];};
 const footer={render:original,invalidate(){}};
 const decoration=mod.createInkFooter(()=>enabled);
 decoration.attach(footer);decoration.attach(footer);
 assert.deepEqual(footer.render(40),['🧠 high']);
 enabled=true;assert.ok(footer.render(40)[0].includes('InkFooter=scroll'));
 decoration.dispose();assert.equal(footer.render,original);
 assert.deepEqual(footer.render(40),['🧠 high']);
});
