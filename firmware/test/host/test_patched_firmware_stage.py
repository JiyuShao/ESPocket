"""The patch build must isolate component-manager mutations from the checkout."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
SPEC = importlib.util.spec_from_file_location('patched_build', ROOT / 'scripts/firmware/build_patched_firmware.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PatchedFirmwareStageTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'checkout'
        self.firmware = self.root / 'firmware'
        self.registry = self.firmware / 'managed_components' / BUILDER.COMPONENT
        self.registry.mkdir(parents=True)
        (self.registry / 'source.txt').write_text('old\n')
        vendor = self.firmware / 'managed_components/vendor/littlefs'
        vendor.mkdir(parents=True)
        (vendor / 'lfs.h').write_text('vendor source\n')
        (self.registry / 'idf_component.yml').write_text('version: 0.8.3\n')
        patches = self.firmware / 'patches' / BUILDER.COMPONENT / BUILDER.VERSION
        patches.mkdir(parents=True)
        patch = patches / '001.patch'
        patch.write_text('--- a/source.txt\n+++ b/source.txt\n@@ -1 +1 @@\n-old\n+new\n')
        (patches / 'manifest.json').write_text(json.dumps({
            'schema_version': 1, 'component': BUILDER.COMPONENT,
            'upstream_version': BUILDER.VERSION,
            'source_files': BUILDER.inventory(self.registry),
            'patches': [{'file': patch.name, 'sha256': BUILDER.digest(patch)}],
        }))
        (self.firmware / 'main').mkdir()
        (self.firmware / 'main/idf_component.yml').write_text(
            'dependencies:\n  espressif/brookesia_runtime_js: "0.8.3"\n')
        (self.firmware / 'dependencies.lock').write_text('registry lock\n')
        self.config = self.base / 'sdkconfig'
        self.config.write_text('CONFIG_EXISTING=y\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=8192\n')
        self.workspace = self.base / 'work'

    def test_stage_isolates_lock_cache_and_config(self):
        before = BUILDER.inventory(self.firmware)
        staged = BUILDER.stage(self.root, self.workspace, self.config)
        self.assertEqual(BUILDER.inventory(self.firmware), before)
        self.assertTrue((staged / 'managed_components/vendor/littlefs/lfs.h').exists())
        self.assertIn('override_path:', (staged / 'main/idf_component.yml').read_text())
        self.assertIn('STACK_SIZE=16384', (staged / 'sdkconfig').read_text())
        self.assertIn('STACK_SIZE=8192', self.config.read_text())
        self.assertEqual((self.workspace / 'patched_components' / BUILDER.COMPONENT / 'source.txt').read_text(), 'new\n')
        (staged / 'dependencies.lock').write_text('changed lock')
        (staged / 'managed_components' / BUILDER.COMPONENT / 'source.txt').unlink()
        self.assertEqual(BUILDER.inventory(self.firmware), before)

    def test_rejects_changed_upstream_before_staging(self):
        (self.registry / 'source.txt').write_text('new upstream\n')
        with self.assertRaisesRegex(ValueError, 'inventory/hash'):
            BUILDER.stage(self.root, self.workspace, self.config)
        self.assertFalse(self.workspace.exists())

    def test_rejects_existing_or_nested_workspace(self):
        self.workspace.mkdir()
        with self.assertRaisesRegex(ValueError, 'new'):
            BUILDER.stage(self.root, self.workspace, self.config)
        with self.assertRaisesRegex(ValueError, 'outside'):
            BUILDER.stage(self.root, self.root / 'nested', self.config)

class RegistryLockTest(unittest.TestCase):
    def test_pins_transitive_versions_without_extra_public_requirements(self):
        text = BUILDER.pin_registry_dependencies('dependencies:\n  vendor/direct: "*"\n', {
            'vendor/direct': {'version': '1.2.3'}, 'vendor/transitive': {'version': '2.3.4~1'},
        })
        self.assertIn('vendor/direct: "1.2.3"', text)
        self.assertIn('version: "2.3.4~1"\n    require: no', text)

    def test_generated_lock_rejects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            original, generated = Path(directory) / 'old', Path(directory) / 'new'
            text = 'dependencies:\n  vendor/lib:\n    component_hash: abc\n    version: 1.0\n'
            original.write_text(text)
            generated.write_text(text)
            BUILDER.verify_registry_lock(original, generated)
            generated.write_text(text.replace('abc', 'changed'))
            with self.assertRaisesRegex(ValueError, 'drift'):
                BUILDER.verify_registry_lock(original, generated)
