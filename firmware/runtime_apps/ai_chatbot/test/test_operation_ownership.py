"""Late action results must not rewrite a newly selected Agent or a newer attempt."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]

class OperationOwnershipTest(unittest.TestCase):
    def test_late_start_and_wake_failures_cannot_rewrite_current_attempt(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
let source=fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
const modulePath=path.join(path.dirname(process.argv[1]),'operations.js');
if(fs.existsSync(modulePath))source=fs.readFileSync(modulePath,'utf8').replace(/^export /gm,'')+'\n'+source;
function fixture(){
 const pending=[];const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{}}});
 vm.runInContext(source,c);c.navigationAlive=true;c.navigationEpoch=1;c.agentReady=true;
 c.internetReady=true;c.agentHandle=10;c.selectedAgentName='A';c.agent=()=>({success:true});
 c.refreshUi=()=>{};c.scheduleLatestHistoryScroll=()=>{};c.hideErrorDialogIfVisible=()=>{};
 c.populateAgentOptions=()=>{};c.callAsync=(h,name,params)=>new Promise(resolve=>pending.push({h,name,params,resolve}));
 const take=action=>{const i=pending.findIndex(p=>p.params.Action===action);assert(i>=0,action);return pending.splice(i,1)[0];};
 return {c,pending,take};
}
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const key=c=>typeof c.statusText==='string'?c.statusText:c.statusText.key;
(async()=>{
 for(const action of ['Activate','Start']){
  const {c,take}=fixture();c.startAgent();const old=take(action);
  assert(c.selectAgent('B'));c.startAgent();const status=key(c);
  old.resolve({success:false,error:'old target'});await flush();
  assert.equal(key(c),status,action+' from old Agent must not overwrite current status');
  // A -> B -> A must not revive the first A operation.
  assert(c.selectAgent('A'));c.startAgent();const latest=key(c);
  const older=take(action);older.resolve({success:false,error:'earlier selection'});await flush();
  assert.equal(key(c),latest,'selection generation must survive A -> B -> A');
 }
 // The first A result remains delayed across A -> B -> A, even with unchanged handle.
 for(const action of ['Activate','Start']){
  const f=fixture();f.c.startAgent();const firstA=f.take(action);
  f.c.selectAgent('B');f.c.selectAgent('A');f.c.startAgent();const status=key(f.c);
  firstA.resolve({success:false,error:'first A'});await flush();assert.equal(key(f.c),status);
 }
 // An acknowledged Start revokes remaining Promise errors without claiming cancellation.
 const acknowledged=fixture();acknowledged.c.startAgent();const late=acknowledged.take('Start');
 acknowledged.c.handleGeneralEventHappened('Started',false);const observed=key(acknowledged.c);
 late.resolve({success:false,error:'late failure'});await flush();assert.equal(key(acknowledged.c),observed);
 // A newer same-kind attempt supersedes both siblings of the older Start.
 const {c,take}=fixture();c.startAgent();const oldActivate=take('Activate'),oldStart=take('Start');
 c.startAgent();const status=key(c);oldActivate.resolve({success:false,error:'old retry'});await flush();
 assert.equal(key(c),status);oldStart.resolve({success:false,error:'old sibling'});await flush();assert.equal(key(c),status);
 take('Activate').resolve({success:true});take('Start').resolve({success:false,error:'current'});await flush();
 assert.equal(key(c),'status.start_failed','current failure remains visible');
 // WakeUp from the first selection must not overwrite a subsequent selection or retry.
 const wake=fixture();wake.c.agentStarted=true;wake.c.agentSleeping=true;wake.c.wakeSleepingAgent();
 const oldWake=wake.take('WakeUp');wake.c.selectAgent('B');wake.c.selectAgent('A');
 wake.c.agentStarted=true;wake.c.agentSleeping=true;wake.c.wakeSleepingAgent();const newStatus=key(wake.c);
 oldWake.resolve({success:false,error:'stale wake'});await flush();assert.equal(key(wake.c),newStatus);
 wake.take('WakeUp').resolve({success:false,error:'current wake'});await flush();assert.equal(key(wake.c),'status.wakeup_failed');
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node','-e',script,str(APP/'src/app/chatbot/lifecycle.js')],check=True)
