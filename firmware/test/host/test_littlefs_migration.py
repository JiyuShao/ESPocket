"""Verify expansion preserves user files and forces Core installation revalidation."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from migrate_littlefs import migrate, inventory


@unittest.skipUnless(importlib.util.find_spec('littlefs'), 'Run with the build littlefs-python environment')
class LittleFSMigrationTest(unittest.TestCase):
    def test_expand_preserves_private_content_and_invalidates_only_core_seals(self):
        from littlefs import LittleFS
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory) / 'backup.bin'
            output = Path(directory) / 'expanded.bin'
            source = LittleFS(block_size=4096, block_count=32, name_max=64)
            source.makedirs('/apps/example.app/data/empty', exist_ok=True)
            source.makedirs('/apps/example.app/files', exist_ok=True)
            contents = {
                '/apps/example.app/manifest.json': b'{"package": {"id": "example.app"}}',
                '/apps/example.app/data/settings.json': b'{"user": "preserved"}',
                '/apps/example.app/files/song.mp3': bytes(range(256)) * 40,
                '/apps/example.app/.brookesia-package.bpk': b'original protected archive',
                '/apps/example.app/.brookesia-verified.json': b'old authenticated receipt',
                '/apps/example.app/data/.brookesia-verified.json': b'user file with matching basename',
            }
            for path, content in contents.items():
                with source.open(path, 'wb') as target:
                    target.write(content)
            before = inventory(source)
            source.unmount()
            original = bytes(source.context.buffer)
            backup.write_bytes(original)
            result = migrate(backup, output, 256 * 1024)
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(result['invalidatedVerificationRecords'], ['/apps/example.app/.brookesia-verified.json'])
            expected = {path: info for path, info in before.items() if path != '/apps/example.app/.brookesia-verified.json'}
            expanded = LittleFS(block_size=4096, block_count=0, mount=False)
            expanded.context.buffer = bytearray(output.read_bytes())
            expanded.mount()
            self.assertEqual(inventory(expanded), expected)
            self.assertIn('empty', expanded.listdir('/apps/example.app/data'))
            self.assertEqual(expanded.block_count * 4096, 256 * 1024)
            self.assertGreater(result['freeBytes'], 128 * 1024)
            with self.assertRaises(ValueError):
                migrate(backup, output, 256 * 1024)
            with self.assertRaises(ValueError):
                migrate(backup, Path(directory) / 'small.bin', len(original))
            with self.assertRaises(ValueError):
                migrate(backup, Path(directory) / 'unaligned.bin', 256 * 1024 + 1)


if __name__ == '__main__':
    unittest.main()
