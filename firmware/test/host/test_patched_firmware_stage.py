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
    def test_display_candidate_adds_only_the_display_patch_to_audio(self):
        audio = BUILDER.PATCH_SETS['audio-candidate']
        self.assertEqual(BUILDER.PATCH_SETS['display-candidate'],
                         audio + (('espressif__brookesia_service_display', '0.8.2'),))
        self.assertNotIn(('espressif__brookesia_service_display', '0.8.2'),
                         BUILDER.PATCH_SETS['baseline'])

    def test_production_promotes_validated_display_and_board_owner_fixes(self):
        self.assertEqual(BUILDER.PATCH_SETS['production'],
                         BUILDER.PATCH_SETS['display-candidate'] + (('espressif__esp_board_manager', '0.5.15'),))

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
        core_component, core_version = BUILDER.PATCHES[1]
        core = self.firmware / 'managed_components' / core_component
        core.mkdir()
        (core / 'source.txt').write_text('old\n')
        core_patches = self.firmware / 'patches' / core_component / core_version
        core_patches.mkdir(parents=True)
        core_patch = core_patches / '001.patch'
        core_patch.write_text(patch.read_text())
        (core_patches / 'manifest.json').write_text(json.dumps({
            'schema_version': 1, 'component': core_component, 'upstream_version': core_version,
            'source_files': BUILDER.inventory(core),
            'patches': [{'file': core_patch.name, 'sha256': BUILDER.digest(core_patch)}],
        }))
        (self.firmware / 'main').mkdir()
        (self.firmware / 'main/idf_component.yml').write_text(
            'dependencies:\n  espressif/brookesia_runtime_js: "0.8.3"\n  espressif/brookesia_system_core: "0.8.4"\n')
        (self.firmware / 'dependencies.lock').write_text('registry lock\n')
        self.config = self.base / 'sdkconfig'
        self.config.write_text('CONFIG_EXISTING=y\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=8192\n')
        self.workspace = self.base / 'work'

    def test_stage_isolates_lock_cache_and_config(self):
        before = BUILDER.inventory(self.firmware)
        staged = BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        self.assertEqual(BUILDER.inventory(self.firmware), before)
        self.assertTrue((staged / 'managed_components/vendor/littlefs/lfs.h').exists())
        self.assertEqual((staged / 'main/idf_component.yml').read_text().count('override_path:'), 2)
        self.assertEqual(len(json.loads((self.workspace / 'patch-inputs.json').read_text())['patches']), 2)
        self.assertEqual((self.workspace / 'patched_components' / BUILDER.PATCHES[1][0] / 'source.txt').read_text(), 'new\n')
        self.assertIn('STACK_SIZE=16384', (staged / 'sdkconfig').read_text())
        self.assertIn('STACK_SIZE=8192', self.config.read_text())
        self.assertEqual((self.workspace / 'patched_components' / BUILDER.COMPONENT / 'source.txt').read_text(), 'new\n')
        (staged / 'dependencies.lock').write_text('changed lock')
        (staged / 'managed_components' / BUILDER.COMPONENT / 'source.txt').unlink()
        self.assertEqual(BUILDER.inventory(self.firmware), before)

    def test_rejects_changed_upstream_before_staging(self):
        (self.registry / 'source.txt').write_text('new upstream\n')
        with self.assertRaisesRegex(ValueError, 'inventory/hash'):
            BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        self.assertFalse(self.workspace.exists())

    def test_rejects_existing_or_nested_workspace(self):
        self.workspace.mkdir()
        with self.assertRaisesRegex(ValueError, 'new'):
            BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        with self.assertRaisesRegex(ValueError, 'outside'):
            BUILDER.stage(self.root, self.root / 'nested', self.config, 'baseline')

    def test_explicit_hal_candidate_isolated_from_production(self):
        component, version = BUILDER.PATCH_SETS['hal-candidate'][-1]
        registry = self.firmware / 'managed_components' / component
        registry.mkdir()
        (registry / 'source.txt').write_text('old\n')
        patches = self.firmware / 'patches' / component / version
        patches.mkdir(parents=True)
        patch = patches / '001.patch'
        patch.write_text('--- a/source.txt\n+++ b/source.txt\n@@ -1 +1 @@\n-old\n+new\n')
        (patches / 'manifest.json').write_text(json.dumps({
            'schema_version': 1, 'component': component, 'upstream_version': version,
            'source_files': BUILDER.inventory(registry),
            'patches': [{'file': patch.name, 'sha256': BUILDER.digest(patch)}],
        }))
        main = self.firmware / 'main/idf_component.yml'
        main.write_text(main.read_text() + '  espressif/brookesia_hal_adaptor:\n    version: "0.8.4"\n    require: no\n')
        before = BUILDER.inventory(self.firmware)
        staged = BUILDER.stage(self.root, self.workspace, self.config, 'hal-candidate')
        self.assertEqual((staged / 'main/idf_component.yml').read_text().count('override_path:'), 3)
        inputs = json.loads((self.workspace / 'patch-inputs.json').read_text())
        self.assertEqual(inputs['patch_set'], 'hal-candidate')
        self.assertIn('override_path: "../../patched_components/espressif__brookesia_hal_adaptor"\n    require: no',
                      (staged / 'main/idf_component.yml').read_text())
        self.assertEqual(inputs['patches'][-1]['component'], component)
        self.assertEqual(BUILDER.inventory(self.firmware), before)

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
            BUILDER.verify_registry_lock(original, generated, 'baseline')
            generated.write_text(text.replace('abc', 'changed'))
            with self.assertRaisesRegex(ValueError, 'drift'):
                BUILDER.verify_registry_lock(original, generated, 'baseline')

    def test_hal_registry_exclusion_requires_explicit_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            original, generated = Path(directory) / 'old', Path(directory) / 'new'
            original.write_text('dependencies:\n  espressif/brookesia_hal_adaptor:\n    component_hash: abc\n    version: 0.8.4\n')
            generated.write_text('dependencies:\n')
            with self.assertRaisesRegex(ValueError, 'drift'):
                BUILDER.verify_registry_lock(original, generated, 'baseline')
            BUILDER.verify_registry_lock(original, generated, 'hal-candidate')


class AudioCandidateConfigTest(unittest.TestCase):
    def test_candidate_overrides_recording_and_preserves_board_settings(self):
        text = BUILDER.configure_audio_candidate('CONFIG_EXISTING=y\nCONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL=y\nCONFIG_AUDIO_AFE_ENABLE=y\n')
        BUILDER.verify_audio_config(text)
        self.assertIn('CONFIG_EXISTING=y', text)
        self.assertNotIn('CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL=y', text)
        self.assertIn('CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT=40', text)
        with self.assertRaisesRegex(ValueError, 'configuration'):
            BUILDER.verify_audio_config(text.replace('BUFFER_HEIGHT=40', 'BUFFER_HEIGHT=50'))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            BUILDER.verify_audio_config(text.replace('# CONFIG_AUDIO_AFE_ENABLE is not set', 'CONFIG_AUDIO_AFE_ENABLE=y'))


    def test_decoder_output_must_match_playback_dac(self):
        text = BUILDER.configure_audio_candidate('')
        # Device trace reproduced 48 kHz mono feeding the locked 16 kHz stereo DAC.
        for name, expected in [
            ('CONFIG_ESP_AUDIO_SIMPLE_PLAYER_RESAMPLE_EN', 'y'),
            ('CONFIG_AUDIO_SIMPLE_PLAYER_RESAMPLE_DEST_RATE', '16000'),
            ('CONFIG_ESP_AUDIO_SIMPLE_PLAYER_CH_CVT_EN', 'y'),
            ('CONFIG_AUDIO_SIMPLE_PLAYER_CH_CVT_DEST', '2'),
            ('CONFIG_ESP_AUDIO_SIMPLE_PLAYER_BIT_CVT_EN', 'y'),
            ('CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_16BIT', 'y'),
        ]:
            self.assertIn(name + '=' + expected, text.splitlines())
        for old, wrong in [
            ('RESAMPLE_DEST_RATE=16000', 'RESAMPLE_DEST_RATE=48000'),
            ('CH_CVT_DEST=2', 'CH_CVT_DEST=1'),
            ('CONFIG_ESP_AUDIO_SIMPLE_PLAYER_CH_CVT_EN=y', '# CONFIG_ESP_AUDIO_SIMPLE_PLAYER_CH_CVT_EN is not set'),
            ('CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_16BIT=y', 'CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_32BIT=y'),
        ]:
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'configuration'):
                BUILDER.verify_audio_config(text.replace(old, wrong))
