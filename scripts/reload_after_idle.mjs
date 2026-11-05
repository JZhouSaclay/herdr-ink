#!/usr/bin/env node
// One-shot reload of this session after the agent settles. No other terminals are touched.
import {execFileSync} from 'node:child_process';
import {writeFileSync,readFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
const [terminal,expectedPid,reportPath]=process.argv.slice(2);
if(!terminal || !/^t[0-9a-z]+$/.test(terminal) || !expectedPid || !reportPath)throw Error('terminal, PID and report path required');
const report={terminal,state:'waiting_for_idle',started:new Date().toISOString()};
const save=()=>writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');save();
const command=(name,args,timeout=15000)=>execFileSync(name,args,{encoding:'utf8',timeout,maxBuffer:2*1024*1024});
try {
  // hc's native wait blocks in this detached helper, never the assistant's tool turn.
  command('/usr/bin/env',['-u','HC_TERMINAL_ID','hc','wait',terminal,'--timeout','600'],620000);
  const facts=JSON.parse(command('hc',['get',terminal]));
  if(String(facts.pid)!==expectedPid || facts.state!=='live' || facts.status?.app!=='pi' || facts.status?.state!=='idle')
    throw Error('Session changed or no longer idle; reload was not sent');
  const lines=command('hc',['read',terminal,'--lines','0']).split(/\r?\n/);
  // In this opt-in ink editor the three rows are blank text; the frame is a Kitty layer.
  // A working caption, draft, modal or unfamiliar footer makes this check fail closed.
  const index=lines.findLastIndex(line=>line.includes('MCP') && line.includes('tok/s'));
  if(index<3 || lines.slice(index-3,index).some(line=>line.trim().length))throw Error('Cannot confirm empty editor; reload was not sent');
  command('/usr/bin/env',['-u','HC_TERMINAL_ID','hc','send','--if','idle',terminal,'/reload']);
  report.state='reload_delivered';report.finished=new Date().toISOString();save();
} catch(error) {
  report.state='not_reloaded';report.reason=String(error.message);report.finished=new Date().toISOString();save();process.exitCode=1;
}
