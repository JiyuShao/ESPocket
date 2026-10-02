"""Exercise the actual JS lifecycle/actions against the public asynchronous port."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[4]

SCRIPT = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const requests = [], ui = [], pending = [];
const scope = {
  console: {log() {}},
  brookesia: {call_service_function(service, operation, json) {ui.push([service, operation, JSON.parse(json)]);}},
  espocketNavigation: {dispatch(json) {
    requests.push(JSON.parse(json));
    return new Promise((resolve, reject) => pending.push({resolve, reject}));
  }}
};
const context = vm.createContext(scope);
const source = fs.readFileSync(process.argv[1], 'utf8');
vm.runInContext(source, context);
const app = scope.brookesia_app;
const state = (token = null) => JSON.stringify({appId:'espocket.app.hello_runtime', pageId:'detail', canBack:token === null, backPending:token !== null, pendingToken:token});
(async () => {
  app.on_start();
  assert.equal(ui.filter(item => item[1] === 'SubscribeAction').length, 4);
  assert(ui.some(item => item[0] === 'SystemTimer' && item[2].IntervalMs === 100));
  let action = app.on_action('open_detail');
  assert.deepEqual(requests.at(-1), {operation:'push', pageId:'detail'});
  pending.shift().resolve(state()); await action;
  action = app.on_action('toggle_confirm');
  assert.equal(requests.at(-1).decision, 'defer');
  pending.shift().resolve(state()); await action;
  const tick = app.on_timer(1, 'navigation');
  await app.on_timer(1, 'navigation'); // Only one in-flight snapshot.
  assert.equal(requests.at(-1).operation, 'snapshot');
  pending.shift().resolve(state('18446744073709551615')); await tick;
  action = app.on_action('cancel_back');
  assert.equal(requests.at(-1).token, '18446744073709551615');
  assert.equal(requests.at(-1).allow, false);
  pending.shift().resolve(state()); await action;
  action = app.on_action('allow_back'); await action;
  assert.equal(ui.at(-1)[2].Text, 'No pending Back');
  action = app.on_action('toggle_confirm');
  app.on_stop(); app.on_start();
  const length = ui.length;
  pending.shift().resolve(state()); await action;
  assert.equal(ui.length, length); // Old async completion cannot mutate new-run UI.
  action = app.on_action('toggle_confirm');
  assert.equal(requests.at(-1).decision, 'defer');
  pending.shift().reject(new Error('back_pending')); await action;
  assert(ui.at(-1)[2].Text.includes('back_pending'));
  action = app.on_action('toggle_confirm');
  assert.equal(requests.at(-1).decision, 'defer'); // A failed change did not commit UI policy.
  pending.shift().resolve(state()); await action;
  action = app.on_action('toggle_confirm');
  app.on_stop();
  vm.runInContext(source, context); // Core can reload the entry in the same JS realm.
  const restarted = scope.brookesia_app;
  assert.notEqual(restarted, app);
  restarted.on_start();
  const restartedUi = ui.length;
  pending.shift().resolve(state()); await action;
  assert.equal(ui.length, restartedUi); // Retired closure cannot write the new GUI.
  action = restarted.on_action('toggle_confirm');
  assert.equal(requests.at(-1).decision, 'defer');
  pending.shift().resolve(state()); await action;
  restarted.on_stop();
})().catch(error => { console.error(error); process.exitCode = 1; });
'''


class RuntimeSampleTest(unittest.TestCase):
    def test_actions_confirmation_and_lifecycle(self):
        subprocess.run(['node', '-e', SCRIPT,
                        str(ROOT / 'firmware/runtime_apps/hello/src/app/main.js')], check=True)


if __name__ == '__main__':
    unittest.main()
