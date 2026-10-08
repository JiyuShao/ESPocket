"""Run the imported Controller's real key actions and arithmetic."""
from pathlib import Path
import subprocess
import unittest

APP = Path(__file__).resolve().parents[1]


class CalculatorTest(unittest.TestCase):
    def test_calculation_delete_percent_and_error_recovery(self):
        script = r'''
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const context = vm.createContext({brookesia: {print: () => {}}});
vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), context);
context.flushUi = () => {};
function keys(...names) { for (const name of names) context.brookesia_app.on_action('calculator.key.' + name); }
keys('clear','digit_1','digit_2','add','digit_3','digit_4','equals');
assert.equal(context.formula, '46');
keys('clear','digit_7','digit_8','digit_9','backspace'); assert.equal(context.formula,'78');
keys('clear','digit_6','digit_0','divide','digit_5','equals'); assert.equal(context.formula,'12');
keys('clear','digit_5','digit_0','percent','equals'); assert.equal(context.formula,'0.5');
keys('clear','digit_1','divide','digit_0','equals'); assert.equal(context.resultText,'Error');
keys('clear','digit_5','multiply','digit_2','equals'); assert.equal(context.formula,'10');
'''
        subprocess.run(['node', '-e', script, str(APP / 'src/app/calculator/lifecycle.js')], check=True)


if __name__ == '__main__':
    unittest.main()
