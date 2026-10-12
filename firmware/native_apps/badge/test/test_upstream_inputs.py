"""Guard the exact upstream inputs and attribution used for migration."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UpstreamInputsTest(unittest.TestCase):
    def test_inventory_and_license_are_complete_and_unchanged(self):
        lock = json.loads((ROOT / 'upstream.lock.json').read_text())
        upstream = ROOT / 'upstream'
        self.assertEqual(len(lock['commit']), 40)
        actual = {str(path.relative_to(upstream)) for path in upstream.rglob('*') if path.is_file()}
        self.assertEqual(actual, set(lock['files']))
        for name, expected in lock['files'].items():
            with self.subTest(name=name):
                data = (upstream / name).read_bytes()
                self.assertEqual(len(data), expected['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected['sha256'])
        self.assertIn('Copyright (c) 2026 curisama', (upstream / 'LICENSE').read_text())
        self.assertIn('NASA', (upstream / 'NOTICE').read_text())
        self.assertIn('Unlicense OR CC0-1.0', (upstream / 'main/ble/esp_hid_gap.c').read_text())
