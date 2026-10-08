"""Product-image updates retain private files and defer trust to Core."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from stage_local_runtime_apps import stage
from migrate_littlefs import inventory


@unittest.skipUnless(importlib.util.find_spec('littlefs'), 'Run with build littlefs-python environment')
class BuiltinUpdateTest(unittest.TestCase):
    def test_preservation_and_revalidation(self):
        from littlefs import LittleFS
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            filesystem = LittleFS(block_size=4096, block_count=256, name_max=64)
            prefix = '/apps/espocket.app.ai_chatbot/'
            contents = {
                '/other/user.bin': b'unrelated',
                prefix + 'data/private.bin': b'private',
                prefix + 'data/README.md': b'user-edited seed',
                prefix + 'files/xiaozhi/0.mp3': b'user-replaced media',
                prefix + 'cache/cache.bin': b'cache',
                prefix + 'files/.brookesia-verified.json': b'user',
                prefix + 'obsolete.js': b'stale',
                prefix + '.brookesia-verified.json': b'old seal',
                prefix + 'manifest.json': json.dumps({'package': {
                    'id': 'espocket.app.ai_chatbot', 'systems': ['espocket']}}).encode(),
            }
            for path, content in contents.items():
                filesystem.makedirs(str(Path(path).parent), exist_ok=True)
                with filesystem.open(path, 'wb') as artifact:
                    artifact.write(content)
            filesystem.unmount()
            backup = directory / 'before.bin'
            backup.write_bytes(bytes(filesystem.context.buffer))
            original = backup.read_bytes()
            with self.assertRaisesRegex(ValueError, 'already exists'):
                stage(backup, directory / 'reject.bin', True)
            output = directory / 'after.bin'
            stage(backup, output, True, True)
            filesystem.context.buffer = bytearray(output.read_bytes())
            filesystem.mount()
            after = inventory(filesystem)
            for path, content in contents.items():
                if any(part in path for part in ('/data/', '/cache/', '/files/')) or path.startswith('/other/'):
                    with filesystem.open(path, 'rb') as artifact:
                        self.assertEqual(artifact.read(), content, path)
            self.assertNotIn(prefix + 'obsolete.js', after)
            self.assertNotIn(prefix + '.brookesia-verified.json', after)
            self.assertEqual(backup.read_bytes(), original)
            with filesystem.open(prefix + '.brookesia-install.json', 'wb') as artifact:
                artifact.write(b'dynamic installation receipt')
            filesystem.unmount()
            dynamic = directory / 'dynamic.bin'
            dynamic.write_bytes(bytes(filesystem.context.buffer))
            with self.assertRaisesRegex(ValueError, 'Dynamic installation'):
                stage(dynamic, directory / 'dynamic-update.bin', True, True)


if __name__ == '__main__':
    unittest.main()
