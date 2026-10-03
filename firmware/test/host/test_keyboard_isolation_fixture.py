"""Exercise fixture verdicts, privacy and brightness restoration in real JS.

This validates the test harness, not Core isolation; the latter needs its
existing real C++ regressions and the explicit device gate.
"""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'firmware/test/device/fixtures/keyboard_isolation'


class KeyboardFixtureTest(unittest.TestCase):
    def test_fixture_detects_delivery_and_does_not_log_text(self):
        script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const root = process.argv[1];
for (const failStop of [false, true]) {
  const lines = [], subscriptions = [];
  const context = vm.createContext({keyboardIsolation: {failStop},
    console: {log: value => lines.push(value)}, brookesia: {
      subscribe_service_event: (...args) => subscriptions.push(args.join('.')),
      call_service_function: () => '{}'
    }});
  vm.runInContext(fs.readFileSync(root + '/observer.js', 'utf8'), context);
  const app = context.brookesia_app;
  app.on_start();
  assert(subscriptions.includes('SystemCore.KeyboardClosed'));
  assert(subscriptions.includes('Display.BacklightBrightnessChanged'));
  app.on_event('SystemCore', 'KeyboardClosed', '{"Text":"NEVER_LOG_THIS"}');
  assert(lines.includes('KISO FAIL_CROSS_OWNER_RESULT')); // Red-capable verdict.
  assert(!lines.some(line => line.includes('NEVER_LOG_THIS')));
  if (failStop) assert.throws(() => app.on_stop(), /KISO_INTENTIONAL_STOP_FAILURE/);
  else app.on_stop();
}
(async () => {
  const lines = [], calls = [], values = [];
  let brightness = 100;
  const context = vm.createContext({console: {log: value => lines.push(value)}, brookesia: {
    subscribe_service_event: () => {}, call_service_function: () => '{}',
    call_service_function_async: async (service, op, raw) => {
      const params = JSON.parse(raw); calls.push(op);
      assert(!['StartApp', 'StopApp'].includes(op), 'Runtime fixture must not coordinate other Apps');
      let data;
      if (op === 'GetOutputs') data = [{id: 1, name: 'Output0'}];
      if (op === 'GetBacklightBrightness') data = brightness;
      if (op === 'SetBacklightBrightness') {brightness = params.Brightness; values.push(brightness);}
      return JSON.stringify({success: true, data});
    }
  }});
  vm.runInContext(fs.readFileSync(root + '/owner.js', 'utf8'), context);
  const app = context.brookesia_app;
  app.on_start();
  for (let round = 0; round < 2; ++round) {
    await app.on_action('open_detail');
    assert.equal(brightness, 100);
    await app.on_event('SystemCore', 'KeyboardClosed', JSON.stringify({Confirmed: true, Text: 'KISO_PRIVATE_PROBE'}));
    assert(lines.includes('KISO OWNER_RESULT ' + round));
  }
  await app.on_action('open_detail');
  assert.equal(calls.filter(op => op === 'ShowKeyboard').length, 2);
  assert(lines.includes('KISO POST_STOP_PUBLIC_DONE'));
  assert.deepEqual(values, [99,100,99,100,99,100]);
  await app.on_event('SystemCore', 'KeyboardClosed', '{"Confirmed":true,"Text":"NEVER_LOG_THIS"}');
  assert(lines.some(line => line.includes('KISO FIXTURE_ERROR')));
  assert(!lines.some(line => line.includes('NEVER_LOG_THIS')));
})().catch(error => {console.error(error);process.exitCode = 1;});
'''
        subprocess.run(['node', '-e', script, str(FIXTURES)], check=True)


if __name__ == '__main__':
    unittest.main()
