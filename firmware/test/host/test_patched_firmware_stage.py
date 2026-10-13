"""The patch build must isolate component-manager mutations from the checkout."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import subprocess
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
SPEC = importlib.util.spec_from_file_location('patched_build', ROOT / 'scripts/firmware/build_patched_firmware.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PatchedFirmwareStageTest(unittest.TestCase):
    def test_storage_configuration_rejects_autoformat_and_small_flash(self):
        configured = BUILDER.configure_storage('CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y\nCONFIG_PARTITION_TABLE_FILENAME="partitions_16m.csv"\nCONFIG_BROOKESIA_HAL_ADAPTOR_STORAGE_FILE_SYSTEM_LITTLEFS_FORMAT_IF_MOUNT_FAILED=y\n')
        BUILDER.verify_storage_config(configured)
        self.assertEqual(BUILDER.configure_storage(configured), configured)
        with self.assertRaises(ValueError):
            BUILDER.verify_storage_config(configured.replace('"32MB"', '"16MB"'))
        with self.assertRaises(ValueError):
            BUILDER.verify_storage_config(configured.replace('# CONFIG_BROOKESIA_HAL_ADAPTOR_STORAGE_FILE_SYSTEM_LITTLEFS_FORMAT_IF_MOUNT_FAILED is not set', 'CONFIG_BROOKESIA_HAL_ADAPTOR_STORAGE_FILE_SYSTEM_LITTLEFS_FORMAT_IF_MOUNT_FAILED=y'))

    def test_performance_configuration_replaces_debug_choice(self):
        configured = BUILDER.configure_performance('CONFIG_COMPILER_OPTIMIZATION_DEBUG=y\n# CONFIG_COMPILER_OPTIMIZATION_PERF is not set\n')
        self.assertIn('CONFIG_COMPILER_OPTIMIZATION_PERF=y\n', configured)
        self.assertNotIn('CONFIG_COMPILER_OPTIMIZATION_DEBUG=y\n', configured)
        self.assertEqual(BUILDER.configure_performance(configured), configured)
        BUILDER.verify_performance_config(configured)
        with self.assertRaisesRegex(ValueError, 'performance'):
            BUILDER.verify_performance_config(configured.replace('CONFIG_LV_FONT_MONTSERRAT_14=y', '# CONFIG_LV_FONT_MONTSERRAT_14 is not set'))

    def test_gui_candidate_aliases_validated_production(self):
        self.assertEqual(BUILDER.PATCH_SETS['gui-candidate'], BUILDER.PATCH_SETS['production'])
        self.assertIn(('espressif__brookesia_gui_lvgl', '0.8.5'), BUILDER.PATCH_SETS['production'])
        self.assertIn(('espressif__brookesia_gui_interface', '0.8.2'), BUILDER.PATCH_SETS['production'])

    def test_scheduler_candidate_selects_only_explicit_core_manifest(self):
        self.assertEqual(BUILDER.PATCH_SETS['scheduler-candidate'], BUILDER.PATCH_SETS['gui-candidate'])
        core_patches = ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4'
        self.assertEqual(json.loads((core_patches / 'scheduler-candidate.json').read_text()),
                         json.loads((core_patches / 'manifest.json').read_text()))
        for patch_set in ('production', 'gui-candidate', 'scheduler-candidate'):
            for component, version in BUILDER.PATCH_SETS[patch_set]:
                expected = 'scheduler-candidate.json' if patch_set == 'scheduler-candidate' and component == 'espressif__brookesia_system_core' else 'manifest.json'
                self.assertEqual(BUILDER.patch_manifest(ROOT, component, version, patch_set).name, expected)

    def test_display_candidate_adds_only_the_display_patch_to_audio(self):
        audio = BUILDER.PATCH_SETS['audio-candidate']
        self.assertEqual(BUILDER.PATCH_SETS['display-candidate'],
                         audio + (('espressif__brookesia_service_display', '0.8.2'),))
        self.assertNotIn(('espressif__brookesia_service_display', '0.8.2'),
                         BUILDER.PATCH_SETS['baseline'])

    def test_production_promotes_validated_display_board_and_store_owner_fixes(self):
        self.assertEqual(BUILDER.PATCH_SETS['production'],
                         BUILDER.PATCH_SETS['display-candidate'] + (('espressif__esp_board_manager', '0.5.15'),
                         ('espressif__brookesia_app_store', '0.8.2'),
                         ('espressif__brookesia_lib_utils', '0.8.2'),
                         ('espressif__brookesia_service_storage', '0.8.3'),
                         ('espressif__brookesia_gui_lvgl', '0.8.5'),
                         ('espressif__esp_lv_decoder', '0.4.3'),
                     ('espressif__esp-boost', '0.6.0'),
                     ('espressif__mcp-c-sdk', '2.0.1'),
                     ('espressif__brookesia_agent_manager', '0.8.2'),
                     ('espressif__brookesia_service_audio', '0.8.2'),
                     ('espressif__esp_xiaozhi', '0.1.2'),
                     ('espressif__esp-sr', '2.4.4')))
        self.assertEqual(BUILDER.PATCH_SETS['store-candidate'], BUILDER.PATCH_SETS['production'])

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
        for component, version in BUILDER.PATCHES[1:]:
            registry = self.firmware / 'managed_components' / component
            registry.mkdir()
            (registry / 'source.txt').write_text('old\n')
            patches = self.firmware / 'patches' / component / version
            patches.mkdir(parents=True)
            component_patch = patches / '001.patch'
            component_patch.write_text(patch.read_text())
            (patches / 'manifest.json').write_text(json.dumps({
                'schema_version': 1, 'component': component, 'upstream_version': version,
                'source_files': BUILDER.inventory(registry),
                'patches': [{'file': component_patch.name, 'sha256': BUILDER.digest(component_patch)}],
            }))
        (self.firmware / 'main').mkdir()
        (self.firmware / 'main/idf_component.yml').write_text(
            'dependencies:\n  espressif/brookesia_runtime_js: "0.8.3"\n  espressif/brookesia_system_core: "0.8.4"\n  espressif/brookesia_gui_interface: "0.8.2"\n')
        (self.firmware / 'dependencies.lock').write_text('registry lock\n')
        self.config = self.base / 'sdkconfig'
        self.config.write_text('CONFIG_EXISTING=y\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=8192\n')
        self.workspace = self.base / 'work'

    def test_stage_isolates_lock_cache_and_config(self):
        before = BUILDER.inventory(self.firmware)
        staged = BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        self.assertEqual(BUILDER.inventory(self.firmware), before)

        self.assertTrue((staged / 'managed_components/vendor/littlefs/lfs.h').exists())
        self.assertEqual((staged / 'main/idf_component.yml').read_text().count('override_path:'), len(BUILDER.PATCHES))
        self.assertEqual(len(json.loads((self.workspace / 'patch-inputs.json').read_text())['patches']), len(BUILDER.PATCHES))
        self.assertEqual((self.workspace / 'patched_components' / BUILDER.PATCHES[1][0] / 'source.txt').read_text(), 'new\n')
        self.assertIn('STACK_SIZE=16384', (staged / 'sdkconfig').read_text())
        self.assertIn('STACK_SIZE=8192', self.config.read_text())
        self.assertEqual((self.workspace / 'patched_components' / BUILDER.COMPONENT / 'source.txt').read_text(), 'new\n')
        (staged / 'dependencies.lock').write_text('changed lock')
        (staged / 'managed_components' / BUILDER.COMPONENT / 'source.txt').unlink()
        self.assertEqual(BUILDER.inventory(self.firmware), before)

    def test_reliability_probe_rejects_conflicting_automatic_fixtures_before_copying(self):
        self.config.write_text('CONFIG_ESPOCKET_M2_LIFECYCLE_STRESS=y\n')
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            BUILDER.stage(self.root, self.workspace, self.config, 'production',
                          reliability_fixture='lifecycle')
        self.assertFalse(self.workspace.exists())
        with self.assertRaisesRegex(ValueError, 'production patch set'):
            BUILDER.stage(self.root, self.workspace, self.config, 'baseline',
                          reliability_fixture='lifecycle')
        self.assertFalse(self.workspace.exists())

    def test_explicit_display_trial_changes_only_copied_configuration(self):
        self.config.write_text(self.config.read_text() + 'CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_REQUIRE_DOUBLE_BUFFER=y\n')
        original = self.config.read_text()
        staged = BUILDER.stage(self.root, self.workspace, self.config, 'baseline',
                               display_buffer_height=80, display_single_buffer=True)
        text = (staged / 'sdkconfig').read_text()
        self.assertIn('BUFFER_HEIGHT=80', text)
        self.assertNotIn('CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_REQUIRE_DOUBLE_BUFFER=y', text)
        self.assertEqual(self.config.read_text(), original)
        inputs = json.loads((self.workspace / 'patch-inputs.json').read_text())
        self.assertEqual(inputs['display_buffer_height'], 80)
        self.assertTrue(inputs['display_single_buffer'])

    def test_generated_board_paths_are_relocated_without_mutating_input(self):
        board = self.firmware / 'components/gen_bmgr_codes'
        board.mkdir(parents=True)
        component = self.firmware / 'managed_components/boards/custom'
        component.mkdir(parents=True)
        original = f'dependencies:\n  custom:\n    override_path: {component}\n'
        (board / 'idf_component.yml').write_text(original)
        staged = BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        self.assertEqual((board / 'idf_component.yml').read_text(), original)
        self.assertIn(str(staged / 'managed_components/boards/custom'),
                      (staged / 'components/gen_bmgr_codes/idf_component.yml').read_text())

    def test_generated_board_unknown_absolute_override_is_rejected(self):
        board = self.firmware / 'components/gen_bmgr_codes'
        board.mkdir(parents=True)
        (board / 'idf_component.yml').write_text('dependencies:\n  custom:\n    override_path: /unknown/old-checkout/custom\n')
        with self.assertRaisesRegex(ValueError, 'outside the isolated'):
            BUILDER.stage(self.root, self.workspace, self.config, 'baseline')

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
        self.assertEqual((staged / 'main/idf_component.yml').read_text().count('override_path:'), len(BUILDER.PATCHES) + 1)
        inputs = json.loads((self.workspace / 'patch-inputs.json').read_text())
        self.assertEqual(inputs['patch_set'], 'hal-candidate')
        self.assertIn('override_path: "../../patched_components/espressif__brookesia_hal_adaptor"\n    require: no',
                      (staged / 'main/idf_component.yml').read_text())
        self.assertEqual(inputs['patches'][-1]['component'], component)
        self.assertEqual(BUILDER.inventory(self.firmware), before)

    def prepare_candidate_fixture(self):
        firmware = BUILDER.stage(self.root, self.workspace, self.config, 'baseline')
        build = firmware / 'build'; build.mkdir()
        images = {'0x0':'bootloader/bootloader.bin', '0x8000':'partition_table/partition-table.bin',
                  '0x10000':'srmodels/srmodels.bin', '0x60000':'espocket.bin', '0xe60000':'littlefs_data.bin'}
        for name in images.values():
            path=build/name;path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(name.encode())
        (build/'flasher_args.json').write_text(json.dumps({'flash_files':images}))
        (build/'flash_args').write_text('\n'.join(f'{offset} {name}' for offset,name in images.items()))
        (build/'project_description.json').write_text(json.dumps({'project_name':'espocket'}))
        (build/'espocket.elf').write_bytes(b'elf')
        return firmware,build,images

    def test_candidate_archives_every_flash_image_and_frozen_inputs(self):
        firmware,build,images=self.prepare_candidate_fixture()
        fingerprint=BUILDER.verify_inputs(self.workspace)
        (self.firmware/'main/idf_component.yml').write_text('checkout changed after staging')
        candidate=BUILDER.archive_candidate(self.workspace)
        manifest=json.loads((candidate/'manifest.json').read_text())
        self.assertEqual(manifest['input_fingerprint'], fingerprint)
        self.assertEqual(manifest['flash_files'], images)
        self.assertFalse(manifest['deployed']);self.assertFalse(manifest['physical_validation'])
        for name,item in manifest['artifacts'].items():
            self.assertEqual(BUILDER.digest(candidate/name),item['sha256'])
            self.assertEqual((candidate/name).stat().st_size,item['bytes'])
        for name in images.values():self.assertEqual((candidate/name).read_bytes(),(build/name).read_bytes())
        self.assertTrue((candidate/'inputs/sdkconfig.original').exists())
        self.assertTrue((candidate/'patches'/BUILDER.COMPONENT/BUILDER.VERSION/'001.patch').exists())
        with self.assertRaises(ValueError):BUILDER.archive_candidate(self.workspace)

    def test_prepare_only_has_no_successful_candidate(self):
        BUILDER.stage(self.root,self.workspace,self.config,'baseline')
        self.assertEqual(json.loads((self.workspace/'input-snapshot.json').read_text())['status'],'prepared')
        self.assertFalse((self.workspace/'candidate').exists())
        with self.assertRaises(OSError):BUILDER.archive_candidate(self.workspace)
        self.assertFalse((self.workspace/'candidate').exists())

    def test_candidate_rejects_missing_flash_image(self):
        _,build,_=self.prepare_candidate_fixture()
        (build/'srmodels/srmodels.bin').unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):BUILDER.archive_candidate(self.workspace)
        self.assertFalse((self.workspace/'candidate').exists())

    def test_candidate_rejects_flash_path_escape(self):
        _,build,_=self.prepare_candidate_fixture()
        for name in ('../outside.bin','/tmp/outside.bin'):
            (build/'flasher_args.json').write_text(json.dumps({'flash_files':{'0x0':name}}))
            with self.assertRaisesRegex(ValueError,'Unsafe'):BUILDER.archive_candidate(self.workspace)
        self.assertFalse((self.workspace/'candidate').exists())

    def test_candidate_rejects_staged_product_and_patched_drift(self):
        firmware,_,_=self.prepare_candidate_fixture()
        product=firmware/'main/new_source.cpp';product.write_text('drift')
        with self.assertRaisesRegex(ValueError,'product_files'):BUILDER.archive_candidate(self.workspace)
        product.unlink()
        patched=self.workspace/'patched_components'/BUILDER.COMPONENT/'source.txt';patched.write_text('drift')
        with self.assertRaisesRegex(ValueError,'patched_files'):BUILDER.archive_candidate(self.workspace)
        self.assertFalse((self.workspace/'candidate').exists())



    def test_failed_idf_build_does_not_publish_candidate(self):
        args = ['build', '--workspace', str(self.workspace), '--sdkconfig', str(self.config), '--patch-set', 'baseline']
        with patch.object(BUILDER, 'ROOT', self.root), patch.object(sys, 'argv', args), \
             patch.object(BUILDER.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'idf.py')):
            with self.assertRaises(SystemExit) as failed:
                BUILDER.main()
        self.assertEqual(failed.exception.code, 1)
        self.assertTrue((self.workspace/'input-snapshot.json').exists())
        self.assertFalse((self.workspace/'candidate').exists())


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
    def test_display_transfer_changes_only_selected_bus_and_rejects_drift(self):
        selected = 'static periph_spi_config_t esp_bmgr_spi_display_cfg = {\n .spi_bus_config = { .max_transfer_sz = 9320, },\n};'
        unrelated = '\nstatic int other_max_transfer_sz = 9320;\n'
        configured = BUILDER.configure_display_transfer(selected + unrelated)
        self.assertIn('.max_transfer_sz = 29824,', configured)
        self.assertTrue(configured.endswith(unrelated))
        self.assertEqual(BUILDER.configure_display_transfer(configured), configured)
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            BUILDER.configure_display_transfer(selected.replace('9320', '1024'))
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            BUILDER.configure_display_transfer(unrelated)

    def test_display_trial_requires_explicit_expected_height_and_keeps_audio_checks(self):
        text = BUILDER.configure_audio_candidate('', display_buffer_height=80)
        BUILDER.verify_audio_config(text, display_buffer_height=80)
        with self.assertRaisesRegex(ValueError, 'configuration'):
            BUILDER.verify_audio_config(text)
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            BUILDER.configure_audio_candidate('', display_buffer_height=50)
        with self.assertRaisesRegex(ValueError, 'configuration'):
            BUILDER.verify_audio_config(text.replace('# CONFIG_AUDIO_AFE_ENABLE is not set',
                                                    'CONFIG_AUDIO_AFE_ENABLE=y'), display_buffer_height=80)

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

    def test_voice_profile_rejects_unavailable_capture_and_format_drift(self):
        playback = BUILDER.configure_audio_candidate('')
        with self.assertRaisesRegex(ValueError, 'configuration'):
            BUILDER.verify_audio_config(playback, voice=True)
        voice = BUILDER.configure_audio_candidate(playback, voice=True)
        BUILDER.verify_audio_config(voice, voice=True)
        self.assertIn('CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_DYNAMIC=y', voice)
        self.assertIn('CONFIG_XIAOZHI_STACK_IN_PSRAM=y', voice)
        self.assertIn('CONFIG_ESP_WIFI_STATIC_TX_BUFFER_NUM=8', voice)
        self.assertIn('CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC=y', voice)
        for old, wrong in (
            ('CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL=y', '# CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL is not set'),
            ('CONFIG_AUDIO_AFE_ENABLE=y', '# CONFIG_AUDIO_AFE_ENABLE is not set'),
            ('CONFIG_AUDIO_ENCODER_OPUS_SUPPORT=y', '# CONFIG_AUDIO_ENCODER_OPUS_SUPPORT is not set'),
            ('CONFIG_XIAOZHI_AUDIO_TASK_STACK_SIZE=8192', 'CONFIG_XIAOZHI_AUDIO_TASK_STACK_SIZE=2048'),
            ('RECORDER_CHANNELS=2', 'RECORDER_CHANNELS=1'),
            ('RECORDER_SAMPLE_RATE=16000', 'RECORDER_SAMPLE_RATE=48000'),
            ('RECORDER_MIC_LAYOUT="MM"', 'RECORDER_MIC_LAYOUT="MR"'),
            ('RECORDER_CHANNEL_GAINS="{}"', 'RECORDER_CHANNEL_GAINS="{\\"0\\":0.0}"'),
            ('CONFIG_XIAOZHI_STACK_IN_PSRAM=y', '# CONFIG_XIAOZHI_STACK_IN_PSRAM is not set'),
            ('CONFIG_ESP_WIFI_STATIC_TX_BUFFER_NUM=8', 'CONFIG_ESP_WIFI_STATIC_TX_BUFFER_NUM=16'),
            ('CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC=y', '# CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC is not set'),
        ):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'configuration'):
                BUILDER.verify_audio_config(voice.replace(old, wrong), voice=True)

    def test_voice_board_input_selects_the_two_physical_microphones(self):
        original = '''const static dev_audio_codec_config_t esp_bmgr_audio_adc_cfg = {
    .name = "audio_adc",
    .chip = "es7210",
    .adc_enabled = true,
    .adc_max_channel = 2,
    .adc_channel_mask = 0x7,
    .adc_channel_labels = "NA,RE,FR,FL",
    .adc_init_gain = 0,
};
'''
        configured = BUILDER.configure_voice_input(original)
        self.assertIn('.adc_channel_mask = 0x3,', configured)
        self.assertIn('.adc_channel_labels = "FL,FR",', configured)
        self.assertIn('.adc_init_gain = 30,', configured)
        self.assertEqual(BUILDER.configure_voice_input(configured), configured)
        for wrong in (original.replace('es7210', 'es8311'), original.replace('0x7', '0xf')):
            with self.assertRaisesRegex(ValueError, 'Unexpected'):
                BUILDER.configure_voice_input(wrong)
