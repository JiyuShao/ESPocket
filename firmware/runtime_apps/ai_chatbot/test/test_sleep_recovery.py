"""Sleep state is truthful and the existing Chat action reaches the real WakeUp Owner."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]


class SleepRecoveryTest(unittest.TestCase):
    def test_sleep_header_wakeup_and_instance_fencing(self):
        script = r'''
const fs=require('fs'), vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{}}});vm.runInContext(source,c);
const calls=[];let completions=[];
c.tr=key=>key;c.localizedText=value=>value.key;c.networkReady=c.internetReady=c.agentReady=true;
c.selectedAgentSupportsChat=()=>true;c.refreshUi=()=>{};c.scheduleLatestHistoryScroll=()=>{};
c.navigatePage=async()=>true;c.hideErrorDialogIfVisible=()=>{};c.resumeAgentIfSuspended=()=>{};
c.renderMissingHistory=()=>{};c.maybeStartAgent=()=>{};
c.callAsync=(_handle,name,params)=>{calls.push(params.Action);return new Promise(resolve=>completions.push(resolve));};
c.navigationAlive=true;c.navigationEpoch=1;
(async()=>{
 c.handleGeneralEventHappened('Started',false);c.handleGeneralEventHappened('Slept',false);
 assert.equal(c.composeHeaderStatus(),'status.agent_sleeping');
 await c.openChatPage('unused');await c.openChatPage('unused');
 assert.deepEqual(calls,['WakeUp']);
 completions.shift()({success:false,error:'offline'});await Promise.resolve();
 await c.openChatPage('unused');assert.deepEqual(calls,['WakeUp','WakeUp']);
 c.handleGeneralEventHappened('Awake',false);
 assert.notEqual(c.composeHeaderStatus(),'status.agent_sleeping');
 // A failed action from the old running instance must not rewrite a restarted instance.
 ++c.navigationEpoch;c.operations.begin("wake");
 completions.shift()({success:false,error:'old'});await Promise.resolve();
 assert.equal(c.operations.pending("wake"),true);
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node', '-e', script, str(APP / 'src/app/chatbot/lifecycle.js')], check=True)


if __name__ == '__main__':
    unittest.main()
