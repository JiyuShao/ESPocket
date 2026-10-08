"""Real binding batches omit unchanged values, retry errors and reset per instance."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]


class BindingUpdatesTest(unittest.TestCase):
    def test_unchanged_retry_and_instance_reset(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{}}});vm.runInContext(source,c);
const batches=[];let succeeds=true;
c.gui=(_name,p)=>{batches.push(p.Commands[0].Params.Updates);return {success:succeeds};};
let updates=[c.bindingUpdate('/title','labelProps.text','chat'),c.bindingUpdate('/status','labelProps.text','ready')];
c.setBindings(updates);c.setBindings(updates);
assert.equal(batches.length,1,'unchanged state must not reapply GUI properties');
c.setBindings([c.bindingUpdate('/status','labelProps.text','speaking')]);
assert.equal(batches[1].length,1);
succeeds=false;c.setBindings([c.bindingUpdate('/status','labelProps.text','listening')]);
succeeds=true;c.setBindings([c.bindingUpdate('/status','labelProps.text','listening')]);
assert.equal(batches.length,4,'failed updates must be retried');
c.localized=(key)=>({key});c.resetRuntimeState();c.setBindings(updates);
assert.equal(batches.length,5,'new running instance must reapply bindings');
'''
        subprocess.run(['node', '-e', script, str(APP / 'src/app/chatbot/lifecycle.js')], check=True)


if __name__ == '__main__':
    unittest.main()
