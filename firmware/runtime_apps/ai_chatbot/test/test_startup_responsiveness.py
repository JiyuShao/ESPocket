"""Slow agent discovery must yield the serialized App execution chain."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]


class StartupResponsivenessTest(unittest.TestCase):
    def test_slow_discovery_does_not_block_start_callback(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
let occupied=0,handles=0,timers=0;
const names=new Map();
const c=vm.createContext({createI18nBundle:()=>({load:()=>({updates:[]})}),brookesia:{
 print:()=>{},start_service:name=>{names.set(++handles,name);return handles;},
 subscribe_event:()=>1,subscribe_service_event:()=>1,
 call_function:(handle,name)=>{
  if(name==='GetAgentAttributes'){occupied+=500;return JSON.stringify({success:true,data:[]});}
  if(name==='GetTargetAgent')return JSON.stringify({success:true,data:''});
  if(name==='GetEnvironment')return JSON.stringify({success:true,data:{language:'en'}});
  return JSON.stringify({success:true,data:++timers});
 },call_function_async:()=>new Promise(()=>{})}});
vm.runInContext(source,c);
assert.equal(c.brookesia_app.on_start(),true);
assert(occupied<=250,`on_start occupies App Owner for ${occupied}ms with slow discovery; PWR/QS cannot run`);
'''
        subprocess.run(['node', '-e', script, str(APP/'src/app/chatbot/lifecycle.js')], check=True)

    def test_discovery_network_single_flight_and_restart_revocation(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
let handle=0,timer=0,occupied=0;const pending=[];
const c=vm.createContext({createI18nBundle:()=>({load:()=>({})}),brookesia:{
 print:()=>{},start_service:()=>++handle,stop_service:()=>{},unsubscribe_event:()=>{},
 subscribe_event:()=>1,subscribe_service_event:()=>1,
 call_function:(_h,name)=>{
  if(['GetAgentAttributes','GetTargetAgent','GetNetworkConnectivityInfo'].includes(name))occupied+=500;
  if(name==='GetAgentAttributes')return JSON.stringify({success:true,data:[]});
  if(name==='GetEnvironment')return JSON.stringify({success:true,data:{language:'en'}});
  return JSON.stringify({success:true,data:++timer});
 },call_function_async:(h,name)=>new Promise(resolve=>pending.push({h,name,resolve}))}});
vm.runInContext(source,c);c.refreshUi=()=>{};let started=0;c.maybeStartAgent=()=>++started;
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const finish=(request,data,success=true)=>request.resolve(JSON.stringify({success,data,error:success?'':'offline'}));
const take=name=>{const i=pending.findIndex(p=>p.name===name);assert(i>=0,name);return pending.splice(i,1)[0];};
(async()=>{
 assert.equal(c.brookesia_app.on_start(),true);const old=take('GetAgentAttributes');
 const networkTick=()=>c.brookesia_app.on_timer(c.networkTimerId,c.NETWORK_TIMER_NAME);
 networkTick();assert(!pending.some(p=>p.name==='GetNetworkConnectivityInfo'));
 c.brookesia_app.on_stop();assert.equal(c.brookesia_app.on_start(),true);
 finish(old,[{Name:'Old'}]);await flush();
 assert(c.operations.pending("discovery") && !c.agentsLoaded && c.agentAttributes.length===0);
 assert(!pending.some(p=>p.name==='GetTargetAgent')); // Old instance must not chain another call.
 finish(take('GetAgentAttributes'),[{Name:'Assistant'}]);await flush();
 const target=take('GetTargetAgent');assert(c.agentAttributes.length===0);
 finish(target,'');await flush();const fallback=take('SetTargetAgent');
 assert(c.agentAttributes.length===0 && !c.agentsLoaded);finish(fallback,null);await flush();
 assert(c.agentsLoaded && !c.operations.pending("discovery") && c.selectedAgentName==='Assistant');
 networkTick();networkTick();const network=take('GetNetworkConnectivityInfo');
 assert(!pending.some(p=>p.name==='GetNetworkConnectivityInfo') && c.operations.pending("network"));
 assert.equal(occupied,0,'slow discovery/network must never run synchronously on the Owner');
 c.brookesia_app.on_stop();c.brookesia_app.on_start();
 finish(network,{InternetReady:true});await flush();
 assert(!c.internetReady && !c.operations.pending("network") && c.operations.pending("discovery") && started===0);
 finish(take('GetAgentAttributes'),null,false);await flush();
 assert(!c.operations.pending("discovery") && !c.agentsLoaded && c.statusText.key==='status.get_agent_list_failed');
 networkTick();assert(!pending.some(p=>p.name==='GetNetworkConnectivityInfo'));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node', '-e', script, str(APP/'src/app/chatbot/lifecycle.js')], check=True)

    def test_configuration_yields_and_cannot_activate_after_stop(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
let occupied=0;const pending=[];
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{},
 call_function:(_h,name)=>{if(name==='SetTargetAgent')occupied+=500;return JSON.stringify({success:true});},
 call_function_async:(_h,name,params)=>new Promise(resolve=>pending.push({name,params:JSON.parse(params),resolve})),
 stop_service:()=>{},unsubscribe_event:()=>{}}});
vm.runInContext(source,c);c.refreshUi=()=>{};
c.navigationAlive=true;c.navigationEpoch=1;c.agentsLoaded=true;c.agentReady=true;
c.internetReady=true;c.selectedAgentName=c.SERVICE_XIAOZHI;c.agentHandle=99;
(async()=>{
 const configuration=c.maybeStartAgent();c.maybeStartAgent();
 assert.equal(occupied,0,'agent configuration must not occupy Owner while its target call is slow');
 const targets=pending.filter(p=>p.name==='SetTargetAgent');assert.equal(targets.length,1);
 c.brookesia_app.on_stop();targets[0].resolve(JSON.stringify({success:true}));await configuration;
 assert(!pending.some(p=>p.params.Action==='Activate' || p.params.Action==='Start'));
 assert(!c.operations.pending("start") && !c.operations.pending("configure"));
 // Exercise navigation/selection revocation and successful async configuration.
 const ready=()=>{c.navigationAlive=true;c.navigationEpoch++;c.agentsLoaded=true;c.agentReady=true;
  c.internetReady=true;c.currentPage=c.PAGE_CHAT;c.selectedAgentName='Configured';c.agentHandle=99;};
 c.selectedAgentConfigFile=()=> 'config.json';
 c.loadSelectedAgentConfig=()=>({success:true,data:{}});
 const take=name=>{const i=pending.findIndex(p=>p.name===name);assert(i>=0,name);return pending.splice(i,1)[0];};
 const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
 pending.length=0;ready();const changed=c.maybeStartAgent();await flush();
 c.selectedAgentName='Other';take('SetAgentInfo').resolve(JSON.stringify({success:true}));await changed;
 assert(!pending.some(p=>p.name==='SetTargetAgent') && !c.operations.pending("configure"));
 ready();const navigated=c.maybeStartAgent();await flush();
 take('SetAgentInfo').resolve(JSON.stringify({success:true}));await flush();
 c.currentPage=c.PAGE_AGENT_SELECT;take('SetTargetAgent').resolve(JSON.stringify({success:true}));await navigated;
 assert(!pending.some(p=>p.params.Action==='Activate') && !c.operations.pending("configure"));
 ready();const started=c.maybeStartAgent();await flush();
 take('SetAgentInfo').resolve(JSON.stringify({success:true}));await flush();
 take('SetTargetAgent').resolve(JSON.stringify({success:true}));await started;
 assert.deepEqual(pending.filter(p=>p.name==='TriggerGeneralAction').map(p=>p.params.Action),['Activate','Start']);
 assert(c.operations.pending("start") && !c.operations.pending("configure"));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node', '-e', script, str(APP/'src/app/chatbot/lifecycle.js')], check=True)

    def test_config_file_read_yields_and_revokes_old_instance(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
let occupied=0;const pending=[];
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{},
 call_function:(_h,name)=>{if(name==='StorageRead')occupied+=500;return JSON.stringify({success:true,data:'{"model":"fixture","api_key":"fixture"}'});},
 call_function_async:(h,name,params)=>new Promise(resolve=>pending.push({h,name,params:JSON.parse(params),resolve})),
 stop_service:()=>{},unsubscribe_event:()=>{}}});
vm.runInContext(source,c);c.refreshUi=()=>{};
const ready=()=>{c.navigationAlive=true;c.navigationEpoch++;c.agentsLoaded=true;c.agentReady=true;
 c.internetReady=true;c.currentPage=c.PAGE_CHAT;c.selectedAgentName=c.SERVICE_OPENAI;c.agentHandle=99;c.coreHandle=88;};
const take=name=>{const i=pending.findIndex(p=>p.name===name);assert(i>=0,name);return pending.splice(i,1)[0];};
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const finish=(p,data)=>p.resolve(JSON.stringify({success:true,data}));
(async()=>{
 ready();const first=c.maybeStartAgent();c.maybeStartAgent();
 assert.equal(occupied,0,'slow config-file read must not occupy the App Owner');
 assert.equal(pending.filter(p=>p.name==='StorageRead').length,1);
 const old=take('StorageRead');assert.equal(old.h,88);assert.equal(old.params.Location.Kind,'AppData');
 c.brookesia_app.on_stop();pending.length=0;ready();const second=c.maybeStartAgent();
 finish(old,'{"model":"old","api_key":"fixture"}');await first;
 assert(!pending.some(p=>p.name==='SetAgentInfo') && c.operations.pending("configure"));
 finish(take('StorageRead'),'{"model":"new","api_key":"fixture"}');await flush();
 const info=take('SetAgentInfo');assert.equal(info.params.Info.model,'new');finish(info,null);await flush();
 finish(take('SetTargetAgent'),null);await second;
 assert.deepEqual(pending.filter(p=>p.name==='TriggerGeneralAction').map(p=>p.params.Action),['Activate','Start']);
 assert(c.operations.pending("start") && !c.operations.pending("configure"));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node', '-e', script, str(APP/'src/app/chatbot/lifecycle.js')], check=True)

    def test_coze_key_read_validation_and_revocation(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
const pending=[];
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{},
 call_function:()=>JSON.stringify({success:true,data:0}),
 call_function_async:(h,name,params)=>new Promise(resolve=>pending.push({h,name,params:JSON.parse(params),resolve})),
 stop_service:()=>{},unsubscribe_event:()=>{}}});
vm.runInContext(source,c);c.refreshUi=()=>{};
const ready=()=>{c.navigationAlive=true;c.navigationEpoch++;c.agentsLoaded=true;c.agentReady=true;
 c.internetReady=true;c.currentPage=c.PAGE_CHAT;c.selectedAgentName=c.SERVICE_COZE;c.agentHandle=99;c.coreHandle=88;};
const take=name=>{const i=pending.findIndex(p=>p.name===name);assert(i>=0,name);return pending.splice(i,1)[0];};
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const finish=(p,data)=>p.resolve(JSON.stringify({success:true,data}));
const config=JSON.stringify({authorization:{app_id:'fixture',public_key:'fixture'},robots:[{name:'fixture',bot_id:'fixture',voice_id:'fixture'}]});
(async()=>{
 ready();const stopped=c.maybeStartAgent();const old=take('StorageRead');
 c.brookesia_app.on_stop();finish(old,config);await stopped;
 assert(!pending.some(p=>p.name==='StorageRead' || p.name==='SetAgentInfo'));
 pending.length=0;ready();const keyStopped=c.maybeStartAgent();
 finish(take('StorageRead'),config);await flush();const key=take('StorageRead');
 assert.equal(key.params.Location.RelativePath,'coze_private_key.pem');
 c.brookesia_app.on_stop();finish(key,'fixture-key');await keyStopped;
 assert(!pending.some(p=>p.name==='SetAgentInfo') && !c.configErrorLatched);
 pending.length=0;ready();const success=c.maybeStartAgent();
 finish(take('StorageRead'),config);await flush();finish(take('StorageRead'),'fixture-key');await flush();
 const info=take('SetAgentInfo');assert.equal(info.params.Info.authorization.private_key,'fixture-key');
 finish(info,null);await flush();finish(take('SetTargetAgent'),null);await success;
 c.brookesia_app.on_stop();pending.length=0;ready();const invalid=c.maybeStartAgent();
 finish(take('StorageRead'),'broken-json');await invalid;
 assert(c.configErrorLatched && c.statusText.key==='status.config_error' && !c.operations.pending("configure"));
 assert(!pending.some(p=>p.name==='SetAgentInfo' || p.params.Action==='Activate'));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        subprocess.run(['node', '-e', script, str(APP/'src/app/chatbot/lifecycle.js')], check=True)
