"""Exercise the actual CLI from outside the checkout, with no physical transport."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
ENTRIES = ('run_device_tests.py', 'interaction_driver.py')


class DeviceTestCliTest(unittest.TestCase):
    def test_help_does_not_need_a_device_or_pyserial(self):
        with tempfile.TemporaryDirectory() as directory:
            for entry in ENTRIES:
                with self.subTest(entry=entry):
                    result = subprocess.run(
                        [sys.executable, '-B', str(ROOT / 'scripts/firmware' / entry), '--help'],
                        cwd=directory, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('--expected-image', result.stdout)
                    self.assertIn('--suite {navigation,cards,surfaces}', result.stdout)

    def test_transport_failure_keeps_evidence_and_legacy_entry_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / 'serial.py').write_text(
                "def Serial(*args, **kwargs):\n    raise OSError('controlled transport failure')\n")
            environment = {**os.environ, 'PYTHONPATH': directory, 'PYTHONDONTWRITEBYTECODE': '1'}
            for entry in ENTRIES:
                with self.subTest(entry=entry):
                    output = temporary / entry
                    result = subprocess.run(
                        [sys.executable, '-B', str(ROOT / 'scripts/firmware' / entry),
                         '--suite', 'cards', '--port', 'fake-port', '--device-id', 'fake-board',
                         '--expected-image', 'fake-image', '--output', str(output),
                         *(['--profile', str(ROOT / 'scripts/firmware/interaction-profile-466.json')]
                           if entry == 'interaction_driver.py' else [])],
                        cwd=directory, env=environment, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    reports = list(output.glob('*/report.json'))
                    self.assertEqual(len(reports), 1)
                    report = json.loads(reports[0].read_text())
                    self.assertEqual(report['status'], 'FAIL')
                    self.assertEqual(report['testSuite'], 'cards')
                    self.assertEqual(report['expectedImage'], 'fake-image')
                    self.assertIn('controlled transport failure', report['error'])
                    self.assertFalse(report['physicalInputVerified'])
                    self.assertFalse(report['visualVerified'])
                    self.assertTrue((reports[0].parent / 'serial.log').is_file())


if __name__ == '__main__':
    unittest.main()
