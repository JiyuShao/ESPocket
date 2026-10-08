"""Test result ownership through the actual App-local module interface."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]

class ChatOperationsTest(unittest.TestCase):
    def test_instance_target_dependency_and_attempt_scopes(self):
        script = r'''
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {createChatOperations}=await import(pathToFileURL(process.argv[1]).href);
let owner={alive:true,instance:1,agent:11,storage:12,device:13,target:'A'};
const ops=createChatOperations(()=>({...owner}));
for(const kind of ['discovery','network','configure','start','wake']){
 const old=ops.begin(kind);assert(ops.current(old)&&ops.pending(kind));
 const newer=ops.begin(kind);assert(!ops.current(old)&&!ops.finish(old));
 assert(ops.pending(kind)&&ops.finish(newer)&&!ops.pending(kind));
}
// Selection changes cancel target work, while discovery/network stay instance-scoped.
const discover=ops.begin('discovery'),network=ops.begin('network');
const configure=ops.begin('configure'),start=ops.begin('start'),wake=ops.begin('wake');
owner.target='B';ops.invalidateAgent();owner.target='A';ops.invalidateAgent();
assert(ops.current(discover)&&ops.current(network));
for(const token of [configure,start,wake])assert(!ops.current(token));
const latest=ops.begin('configure');assert(!ops.finish(configure)&&ops.pending('configure'));
owner.storage=99;assert(!ops.current(latest)&&!ops.pending('configure'));
const device=ops.begin('network');owner.agent=22;assert(ops.current(device));
const target=ops.begin('start');owner.agent=33;assert(!ops.current(target));
owner.device=44;assert(!ops.current(device));
for(const kind of ['discovery','network','configure','start','wake']){
 const ticket=ops.begin(kind);owner.instance++;assert(!ops.current(ticket));
 const next=ops.begin(kind);owner.alive=false;assert(!ops.current(next));owner.alive=true;
 ops.reset();assert(!ops.current(next)&&!ops.pending(kind));
}
const acknowledged=ops.begin('start');ops.clear('start');assert(!ops.current(acknowledged));
assert.throws(()=>ops.begin('unknown'));
'''
        subprocess.run(['node','--input-type=module','-e',script,str(APP/'src/app/chatbot/operations.js')],check=True)
