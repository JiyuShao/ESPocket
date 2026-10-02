"""Reclaim expectations differ from ordinary wake and from the unselected model."""
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from firmware.test.device.e2e import reclaim
from firmware.test.device.support.usb_test_client import DeviceTestError


class Recording:
    def __init__(self, busy=False):
        self.busy = busy
        self.steps = {}
    def snapshot(self):
        return {'inputBusy': self.busy, 'display': True, 'surface': 'watch_face', 'foregroundAppId': ''}
    def touch(self, name, expected, *points):
        self.steps[name] = expected
    power = touch
    def await_state(self, name, expected, **options):
        self.steps[name] = expected


class ReclaimScenarioTest(unittest.TestCase):
    def test_selected_and_unselected_models(self):
        profile = json.loads((ROOT / 'firmware/test/device/profiles/circular-466.json').read_text())
        for selected in ('native', 'runtime'):
            with self.subTest(selected=selected):
                runner = Recording()
                reclaim.run(runner, profile, selected)
                self.assertEqual(runner.steps[selected + ' reclaimed while off']['pageId'], '')
                self.assertFalse(runner.steps[selected + ' reclaimed while off']['display'])
                self.assertEqual(runner.steps[selected + ' relaunch starts Root']['pageId'], 'root')
                self.assertFalse(runner.steps[selected + ' old confirmation state cleared']['backPending'])
                other = 'runtime' if selected == 'native' else 'native'
                self.assertEqual(runner.steps[other + ' unaffected wake preserves Detail']['pageId'], 'detail')
    def test_busy_device_gets_no_stimuli(self):
        runner = Recording(busy=True)
        with self.assertRaises(DeviceTestError):
            reclaim.run(runner, {}, 'native')
        self.assertEqual(runner.steps, {})
