"""Exercise the real Chat refresh for both product palettes and nav states."""
import json
from pathlib import Path
import re
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[2]


class ThemeBindingsTest(unittest.TestCase):
    def test_resources_and_dynamic_navigation_use_both_palettes(self):
        text = (APP/'src/res/root.json').read_text()
        tokens = set(re.findall(r'\$\{color\.([^}]+)\}', text))
        self.assertFalse(re.search(r'#[0-9A-Fa-f]{6}', text))
        themes = {}
        for name in ('dark', 'light'):
            colors = json.loads((ROOT/f'firmware/components/espocket_system/resources/{name}_theme.json').read_text())['assets'][0]['data']['colors']
            flat = {group+'.'+key: value for group, values in colors.items() for key, value in values.items()}
            self.assertTrue(tokens <= flat.keys())
            themes[name] = flat
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(require('path').join(require('path').dirname(process.argv[1]),'operations.js'),'utf8').replace(/^export /gm,'')+'\n'+fs.readFileSync(process.argv[1],'utf8').replace(/^import[^\n]+\n/gm,'');
const c=vm.createContext({createI18nBundle:()=>({}),brookesia:{print:()=>{}}});vm.runInContext(source,c);
c.tr=k=>k;c.localizedText=k=>k;c.composeHeaderStatus=()=>'';c.selectedAgentSupportsChat=()=>false;
let batch;c.setBindings=u=>{batch=u;};
const themes=JSON.parse(process.argv[2]);
function lookup(path,field){const u=batch.find(x=>x.Path===path && x.Key===field);assert(u);return u.Value;}
for(const palette of Object.values(themes)){
 function resolve(value){const m=/^\$\{color\.([^}]+)\}$/.exec(value);assert(m,'refresh must not overwrite theme with a literal');assert(palette[m[1]]);return palette[m[1]];}
 for(const page of [c.PAGE_CHAT,c.PAGE_SETTINGS]){
  c.currentPage=page;c.refreshUi();
  for(const u of batch.filter(u=>/Color$|Recolor$/.test(u.Key)))resolve(u.Value);
  const active=page===c.PAGE_CHAT?c.CHROME_NAV_CHAT_PILL_PATH:c.CHROME_NAV_SETTINGS_PILL_PATH;
  const label=page===c.PAGE_CHAT?c.CHROME_NAV_CHAT_LABEL_PATH:c.CHROME_NAV_SETTINGS_LABEL_PATH;
  assert.equal(resolve(lookup(active,'style.bgColor')),palette['primary.fill']);
  assert.equal(resolve(lookup(label,'style.textColor')),palette['primary.on']);
 }
}
'''
        subprocess.run(['node','-e',script,str(APP/'src/app/chatbot/lifecycle.js'),json.dumps(themes)],check=True)


if __name__ == '__main__':
    unittest.main()
