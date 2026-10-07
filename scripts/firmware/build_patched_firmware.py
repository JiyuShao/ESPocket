#!/usr/bin/env python3
"""Build the accepted patch baseline in an isolated firmware project copy."""

import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys

from prepare_patched_component import digest, inventory, prepare
from check_glyphs import check as check_glyphs

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = 'espressif__brookesia_runtime_js'
VERSION = '0.8.3'
PATCHES = ((COMPONENT, VERSION), ('espressif__brookesia_system_core', '0.8.4'))
PATCH_SETS = {
    'baseline': PATCHES,
    'production': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3'), ('espressif__brookesia_service_display', '0.8.2'), ('espressif__esp_board_manager', '0.5.15'), ('espressif__brookesia_app_store', '0.8.2'), ('espressif__brookesia_lib_utils', '0.8.2'), ('espressif__brookesia_service_storage', '0.8.3'), ('espressif__brookesia_gui_lvgl', '0.8.5'), ('espressif__brookesia_gui_interface', '0.8.2'), ('espressif__esp_lv_decoder', '0.4.3'), ('espressif__esp-boost', '0.6.0')),
    'hal-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'),),
    'audio-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3')),
    'display-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3'), ('espressif__brookesia_service_display', '0.8.2')),
}

PATCH_SETS['production'] += (('espressif__mcp-c-sdk', '2.0.1'),)
PATCH_SETS['production'] += (('espressif__brookesia_agent_manager', '0.8.2'),)
PATCH_SETS['production'] += (('espressif__esp_xiaozhi', '0.1.2'),)
PATCH_SETS['production'] += (('espressif__esp-sr', '2.4.4'),)
PATCH_SETS['gui-candidate'] = PATCH_SETS['production']
PATCH_SETS['scheduler-candidate'] = PATCH_SETS['gui-candidate']

# Keep the explicit candidate entry for reproducible historical commands.
PATCH_SETS['store-candidate'] = PATCH_SETS['production']


AUDIO_OPTIONS = {
    'CONFIG_SPIRAM_XIP_FROM_PSRAM': False,
    'CONFIG_SPIRAM_FETCH_INSTRUCTIONS': False,
    'CONFIG_SPIRAM_RODATA': False,
    'CONFIG_BROOKESIA_SERVICE_HTTP_WORKER_NUM': 2,
    'CONFIG_BROOKESIA_SERVICE_HTTP_MAX_CONCURRENT_REQUESTS': 1,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_ENABLE_AUDIO_DEVICE': True,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_PLAYER_IMPL': True,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL': False,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_PROCESSOR_IMPL': True,
    'CONFIG_BROOKESIA_SERVICE_AUDIO_ENABLE_AUTO_REGISTER': True,
    # Match the locked AudioProcessorPlaybackConfig DAC (16 kHz, stereo, 16 bit).
    # Simple-player's defaults otherwise resample to 48 kHz without channel conversion.
    'CONFIG_ESP_AUDIO_SIMPLE_PLAYER_RESAMPLE_EN': True,
    'CONFIG_AUDIO_SIMPLE_PLAYER_RESAMPLE_DEST_RATE': 16000,
    'CONFIG_ESP_AUDIO_SIMPLE_PLAYER_CH_CVT_EN': True,
    'CONFIG_AUDIO_SIMPLE_PLAYER_CH_CVT_DEST': 2,
    'CONFIG_ESP_AUDIO_SIMPLE_PLAYER_BIT_CVT_EN': True,
    'CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_16BIT': True,
    'CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_24BIT': False,
    'CONFIG_AUDIO_SIMPLE_PLAYER_BIT_CVT_DEST_32BIT': False,
    'CONFIG_VIDEO_PROCESSOR_ENABLE': False,
    'CONFIG_AUDIO_AFE_ENABLE': False,
    'CONFIG_MEDIA_DUMP_ENABLE': False,
    # 466px Generic output needs two internal buffers; keep them below the measured 80KiB block.
    'CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT': 40,
}

VOICE_OPTIONS = {
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_ENABLE_CODEC_RECORDER_IMPL': True,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_BITS': 16,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_CHANNELS': 2,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_SAMPLE_RATE': 16000,
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_MIC_LAYOUT': '"MM"',
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_GENERAL_GAIN': '"30.0"',
    'CONFIG_BROOKESIA_HAL_ADAPTOR_AUDIO_CODEC_RECORDER_CHANNEL_GAINS': '"{}"',
    'CONFIG_AUDIO_AFE_ENABLE': True,
    'CONFIG_AUDIO_ENCODER_OPUS_SUPPORT': True,
    'CONFIG_AUDIO_DECODER_OPUS_SUPPORT': True,
    'CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_STATIC': False,
    'CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_DYNAMIC': True,
    'CONFIG_XIAOZHI_STACK_IN_PSRAM': True,
    'CONFIG_XIAOZHI_AUDIO_TASK_STACK_SIZE': 8192,
    'CONFIG_ESP_WIFI_STATIC_RX_BUFFER_NUM': 10,
    'CONFIG_ESP_WIFI_STATIC_TX_BUFFER_NUM': 8,
    'CONFIG_ESP_WIFI_TX_BA_WIN': 6,
    'CONFIG_MBEDTLS_INTERNAL_MEM_ALLOC': False,
    'CONFIG_MBEDTLS_EXTERNAL_MEM_ALLOC': True,
    'CONFIG_MBEDTLS_DEFAULT_MEM_ALLOC': False,
    'CONFIG_MBEDTLS_CUSTOM_MEM_ALLOC': False,
}

VOICE_PATCH_SETS = frozenset(('production', 'store-candidate', 'gui-candidate', 'scheduler-candidate'))

STORAGE_OPTIONS = {
    'CONFIG_ESPTOOLPY_FLASHSIZE_16MB': False,
    'CONFIG_ESPTOOLPY_FLASHSIZE_32MB': True,
    'CONFIG_ESPTOOLPY_FLASHSIZE': '"32MB"',
    'CONFIG_PARTITION_TABLE_CUSTOM': True,
    'CONFIG_PARTITION_TABLE_CUSTOM_FILENAME': '"partitions_32m.csv"',
    'CONFIG_PARTITION_TABLE_FILENAME': '"partitions_32m.csv"',
    'CONFIG_BROOKESIA_HAL_ADAPTOR_STORAGE_FILE_SYSTEM_LITTLEFS_FORMAT_IF_MOUNT_FAILED': False,
}

PERFORMANCE_OPTIONS = {
    'CONFIG_COMPILER_OPTIMIZATION_DEBUG': False,
    'CONFIG_COMPILER_OPTIMIZATION_SIZE': False,
    'CONFIG_COMPILER_OPTIMIZATION_PERF': True,
    'CONFIG_COMPILER_OPTIMIZATION_NONE': False,
    'CONFIG_LV_FONT_MONTSERRAT_10': True,
    'CONFIG_LV_FONT_MONTSERRAT_12': True,
    'CONFIG_LV_FONT_MONTSERRAT_14': True,
    'CONFIG_LV_FONT_MONTSERRAT_16': True,
}

DISPLAY_TRANSFER_BYTES = 466 * 32 * 2


def configure_display_transfer(text):
    pattern = re.compile(r'(static periph_spi_config_t esp_bmgr_spi_display_cfg = \{.*?\.max_transfer_sz = )(\d+)(,.*?\n\};)', re.DOTALL)
    matched = pattern.search(text)
    if not matched or int(matched[2]) not in (9320, DISPLAY_TRANSFER_BYTES):
        raise ValueError('Unexpected generated display SPI configuration')
    return text[:matched.start()] + matched[1] + str(DISPLAY_TRANSFER_BYTES) + matched[3] + text[matched.end():]


def configure_voice_input(text):
    pattern = re.compile(r'const static dev_audio_codec_config_t esp_bmgr_audio_adc_cfg = \{.*?\n\};', re.DOTALL)
    matched = pattern.search(text)
    if not matched:
        raise ValueError('Unexpected generated audio ADC configuration')
    original = matched[0]
    values = {
        'chip': ('"es7210"', '"es7210"'),
        'adc_enabled': ('true', 'true'),
        'adc_max_channel': ('2', '2'),
        'adc_channel_mask': ('0x7', '0x3'),
        'adc_channel_labels': ('"NA,RE,FR,FL"', '"FL,FR"'),
        'adc_init_gain': ('0', '30'),
    }
    configured = original
    for name, (previous, expected) in values.items():
        field = re.compile(r'(\.' + name + r' = )([^\n]+)(,\n)')
        selected = field.search(configured)
        if not selected or selected[2] not in (previous, expected):
            raise ValueError(f'Unexpected generated audio ADC configuration: {name}')
        configured = field.sub(lambda selection: selection[1] + expected + selection[3], configured, count=1)
    return text[:matched.start()] + configured + text[matched.end():]


def configure_performance(text):
    lines = [line for line in text.splitlines()
             if not any(line.startswith(key + '=') or line == '# ' + key + ' is not set'
                        for key in PERFORMANCE_OPTIONS)]
    for key, enabled in PERFORMANCE_OPTIONS.items():
        lines.append(key + '=y' if enabled else '# ' + key + ' is not set')
    return '\n'.join(lines) + '\n'


def verify_performance_config(text):
    for key, enabled in PERFORMANCE_OPTIONS.items():
        expected = key + '=y' if enabled else '# ' + key + ' is not set'
        if expected not in text.splitlines():
            raise ValueError(f'Incomplete product performance configuration: {key}')


def configure_storage(text):
    lines = [line for line in text.splitlines()
             if not any(line.startswith(key + '=') or line == '# ' + key + ' is not set'
                        for key in STORAGE_OPTIONS)]
    for key, value in STORAGE_OPTIONS.items():
        lines.append(key + '=y' if value is True else '# ' + key + ' is not set' if value is False else key + '=' + value)
    return '\n'.join(lines) + '\n'


def verify_storage_config(text):
    for key, value in STORAGE_OPTIONS.items():
        expected = key + '=y' if value is True else '# ' + key + ' is not set' if value is False else key + '=' + value
        if expected not in text.splitlines():
            raise ValueError(f'Unsafe or incomplete storage configuration: {key}')


def audio_dependencies(root):
    path = root / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/audio-candidate-dependencies.json'
    document = json.loads(path.read_text())
    if document['schema_version'] != 1:
        raise ValueError('Unknown audio candidate dependency schema')
    dependencies = dict(document['dependencies'])
    store_path = root / 'firmware/store-app-dependencies.json'
    if store_path.exists():
        store = json.loads(store_path.read_text())
        if store['schema_version'] != 1 or set(dependencies) & set(store['dependencies']):
            raise ValueError('Invalid Store dependency identities')
        dependencies.update(store['dependencies'])
    return dependencies


def display_options(display_buffer_height, *, voice=False):
    if display_buffer_height not in (40, 80):
        raise ValueError('Unsupported display buffer height')
    return {**AUDIO_OPTIONS, **(VOICE_OPTIONS if voice else {}),
            'CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT': display_buffer_height}


def configure_audio_candidate(text, *, display_buffer_height=40, voice=False):
    options = display_options(display_buffer_height, voice=voice)
    lines = [line for line in text.splitlines() if not any(
        line.startswith(key + '=') or line.startswith('# ' + key + ' ')
        for key in options)]
    for key, enabled in options.items():
        if type(enabled) is bool:
            lines.append(key + '=y' if enabled else '# ' + key + ' is not set')
        else:
            lines.append(key + '=' + str(enabled))
    return '\n'.join(lines) + '\n'


def verify_audio_config(text, *, display_buffer_height=40, voice=False):
    options = display_options(display_buffer_height, voice=voice)
    for key, enabled in options.items():
        if type(enabled) is bool:
            valid = (key + '=y' in text.splitlines()) == enabled
        else:
            valid = key + '=' + str(enabled) in text.splitlines()
        if not valid:
            raise ValueError(f'Unsafe or incomplete audio candidate configuration: {key}')


def registry_lock(path):
    entries = {}
    for match in re.finditer(r'^  ([^ \n]+):\n(.*?)(?=^  [^ \n]+:|^\S|\Z)',
                             path.read_text(), re.MULTILINE | re.DOTALL):
        name, body = match.groups()
        version = re.search(r'^    version: (.+)$', body, re.MULTILINE)
        checksum = re.search(r'^    component_hash: (.+)$', body, re.MULTILINE)
        if checksum and version:
            entries[name] = {'version': version[1], 'component_hash': checksum[1]}
    return entries


def pin_registry_dependencies(text, locked):
    for name, identity in locked.items():
        # Existing direct dependencies retain their visibility. New constraints only pin versions.
        pattern = re.compile(r'^  ' + re.escape(name) + r': [^\n]+$', re.MULTILINE)
        if pattern.search(text):
            text = pattern.sub(f'  {name}: "{identity["version"]}"', text)
        elif f'  {name}:\n' not in text:
            text += f'  {name}:\n    version: "{identity["version"]}"\n    require: no\n'
    return text


def verify_registry_lock(original, generated, patch_set='production', root=ROOT):
    expected = registry_lock(original)
    actual = registry_lock(generated)
    if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate', 'gui-candidate', 'scheduler-candidate'):
        extra = audio_dependencies(root)
        if set(expected) & set(extra):
            raise ValueError('Audio dependency constraints overlap production')
        expected.update(extra)
    for component, _ in PATCH_SETS[patch_set]:
        expected.pop(component.replace('__', '/'), None)
    if actual != expected:
        changed = sorted(name for name in set(actual) | set(expected)
                         if actual.get(name) != expected.get(name))
        raise ValueError(f'Unexpected registry dependency drift: {changed}')


def patch_manifest(root, component, version, patch_set):
    filename = 'scheduler-candidate.json' if patch_set == 'scheduler-candidate' and component == 'espressif__brookesia_system_core' else 'manifest.json'
    return root / 'firmware/patches' / component / version / filename


def stage(root, workspace, sdkconfig, patch_set='production', *, display_buffer_height=40, display_single_buffer=False):
    source_spelling = str(root / 'firmware')
    root = root.resolve()
    source = root / 'firmware'
    workspace = workspace.resolve()
    if workspace.exists():
        raise ValueError('Workspace must be new; preserve previous build evidence')
    if workspace == root or root in workspace.parents or workspace in root.parents:
        raise ValueError('Workspace must be outside the source checkout')
    manifests = []
    for component, version in PATCH_SETS[patch_set]:
        registry = source / 'managed_components' / component
        manifest = patch_manifest(root, component, version, patch_set)
        locked = json.loads(manifest.read_text())
        if locked['component'] != component or locked['upstream_version'] != version:
            raise ValueError('Unexpected patch identity')
        if inventory(registry) != locked['source_files']:
            raise ValueError('Locked source inventory/hash mismatch')
        manifests.append((component, version, registry, manifest, locked))
    workspace.mkdir(parents=True)
    firmware = workspace / 'firmware'
    # Real copies: the component manager may rewrite lockfiles or delete unused caches.
    def ignore_generated(directory, names):
        ignored = {'node_modules', '__pycache__'}
        if Path(directory) == source:
            ignored |= {'build', 'sdkconfig', 'sdkconfig.old', 'littlefs'}
        return set(names) & ignored

    shutil.copytree(source, firmware, ignore=ignore_generated)
    # Board Manager emits absolute component paths. Keep the copied board input
    # inside this workspace, rather than selecting a component from the checkout.
    generated_board = firmware / 'components/gen_bmgr_codes'
    audio_devices = generated_board / 'gen_board_device_config.c'
    if audio_devices.is_file() and patch_set in VOICE_PATCH_SETS:
        audio_devices.write_text(configure_voice_input(audio_devices.read_text()))
    display_peripheral = generated_board / 'gen_board_periph_config.c'
    if display_peripheral.is_file() and patch_set == 'production':
        display_peripheral.write_text(configure_display_transfer(display_peripheral.read_text()))
    for name in ('CMakeLists.txt', 'idf_component.yml', 'board_manager.defaults'):
        generated = generated_board / name
        if generated.is_file():
            generated.write_text(generated.read_text().replace(source_spelling, str(firmware)).replace(str(source), str(firmware)))
    board_manifest = generated_board / 'idf_component.yml'
    if board_manifest.is_file():
        for match in re.finditer(r'^\s+override_path: ["\']?(/[^"\'\n]+)',
                                 board_manifest.read_text(), re.MULTILINE):
            selected_board_component = Path(match[1]).resolve()
            if not selected_board_component.is_relative_to(firmware):
                raise ValueError('Generated board override is outside the isolated firmware; regenerate board configuration')
    shutil.copyfile(sdkconfig, firmware / 'sdkconfig')
    main_manifest = firmware / 'main/idf_component.yml'
    constraints = registry_lock(source / 'dependencies.lock')
    audio_extra = audio_dependencies(root) if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate', 'gui-candidate', 'scheduler-candidate') else {}
    if set(constraints) & set(audio_extra):
        raise ValueError('Audio dependency constraints overlap production')
    constraints.update(audio_extra)
    text = pin_registry_dependencies(main_manifest.read_text(), constraints)
    patch_inputs = []
    for component, version, registry, manifest, locked in manifests:
        patched = prepare(registry, manifest, workspace / 'patched_components' / component)
        dependency = component.replace('__', '/')
        original = f'  {dependency}: "{version}"\n'
        structured = f'  {dependency}:\n    version: "{version}"\n    require: no\n'
        override = (f'  {dependency}:\n'
                    f'    version: "{version}"\n'
                    f'    override_path: "../../patched_components/{component}"\n')
        if text.count(original) == 1:
            text = text.replace(original, override)
        elif text.count(structured) == 1:
            text = text.replace(structured, override + '    require: no\n')
        else:
            raise ValueError(f'Main manifest no longer matches locked patch version: {dependency}')
        patch_inputs.append({'component': component, 'version': version,
                             'manifest_sha256': digest(manifest), 'manifest_file': manifest.name, 'source_files': locked['source_files'],
                             'patched_component': str(patched)})
    main_manifest.write_text(text)
    config = firmware / 'sdkconfig'
    if patch_set == 'production':
        config.write_text(configure_storage(config.read_text()))
    if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate', 'gui-candidate', 'scheduler-candidate'):
        config.write_text(configure_audio_candidate(config.read_text(), display_buffer_height=display_buffer_height,
                                                   voice=patch_set in VOICE_PATCH_SETS))
        config.write_text(configure_performance(config.read_text()))
    elif display_buffer_height != 40:
        display_options(display_buffer_height)
        lines = [line for line in config.read_text().splitlines()
                 if 'CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT' not in line]
        config.write_text('\n'.join(lines) + f'\nCONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT={display_buffer_height}\n')
    if display_single_buffer:
        lines = [line for line in config.read_text().splitlines()
                 if 'CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_REQUIRE_DOUBLE_BUFFER' not in line]
        config.write_text('\n'.join(lines) + '\n# CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_REQUIRE_DOUBLE_BUFFER is not set\n')
    lines = [line for line in config.read_text().splitlines()
             if 'CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE' not in line]
    config.write_text('\n'.join(lines) + '\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=16384\n')
    (workspace / 'patch-inputs.json').write_text(json.dumps({
        'patch_set': patch_set,
        'voice_enabled': patch_set in VOICE_PATCH_SETS,
        'product_display_transfer_bytes': DISPLAY_TRANSFER_BYTES if patch_set == 'production' else None,
        'audio_candidate_dependencies': audio_extra,
        'display_buffer_height': next((int(line.split('=')[1]) for line in config.read_text().splitlines()
                                      if line.startswith('CONFIG_BROOKESIA_GUI_LVGL_DISPLAY_SOURCE_BUFFER_HEIGHT=')), None),
        'display_single_buffer': display_single_buffer,
        'patches': patch_inputs,
        'sdkconfig_input_sha256': digest(sdkconfig), 'async_stack_bytes': 16384,
        'original_registry_lock_sha256': digest(source / 'dependencies.lock'),
        'firmware_project': str(firmware),
    }, indent=2) + '\n')
    return firmware


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--sdkconfig', required=True, type=Path,
                        help='existing board-configured sdkconfig; copied with documented patch-set settings')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--patch-set', choices=PATCH_SETS, default='production',
                        help='production includes accepted display/audio fixes; baseline preserves the prior minimal patch set; candidates are explicit subsets')
    parser.add_argument('--display-buffer-height', type=int, choices=(40, 80), default=40, help='explicit display buffer trial; product default is 40')
    parser.add_argument('--display-single-buffer', action='store_true', help='explicit single-buffer trial; otherwise preserve board buffering')
    args = parser.parse_args()
    try:
        firmware = stage(ROOT, args.workspace, args.sdkconfig.resolve(), args.patch_set, display_buffer_height=args.display_buffer_height, display_single_buffer=args.display_single_buffer)
        print(f'Prepared firmware: {firmware}', flush=True)
        if not args.prepare_only:
            subprocess.run(['idf.py', '-C', str(firmware), 'reconfigure'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock', args.patch_set)
            if args.patch_set == 'production':
                verify_storage_config((firmware / 'sdkconfig').read_text())
                verify_performance_config((firmware / 'sdkconfig').read_text())
            if args.patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate', 'gui-candidate', 'scheduler-candidate'):
                verify_audio_config((firmware / 'sdkconfig').read_text(), display_buffer_height=args.display_buffer_height,
                                    voice=args.patch_set in VOICE_PATCH_SETS)
            if args.patch_set in VOICE_PATCH_SETS:
                generated_audio = firmware / 'components/gen_bmgr_codes/gen_board_device_config.c'
                configured_audio = generated_audio.read_text()
                if configure_voice_input(configured_audio) != configured_audio:
                    raise ValueError('Configured product microphone channels changed after reconfigure')
            glyph_errors = check_glyphs(args.workspace.resolve(), (firmware / 'sdkconfig').read_text())
            if glyph_errors:
                raise ValueError('Configured glyph coverage failed: ' + '\n'.join(glyph_errors))
            description = json.loads((firmware / 'build/project_description.json').read_text())
            for component, _ in PATCH_SETS[args.patch_set]:
                selected = description['build_component_info'][component]['dir']
                expected = args.workspace.resolve() / 'patched_components' / component
                if Path(selected).resolve() != expected:
                    raise ValueError(f'Build selected unexpected patched source: {selected}')
            subprocess.run(['idf.py', '-C', str(firmware), 'build'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock', args.patch_set)
            print(f'Verified patched components: {[item[0] for item in PATCH_SETS[args.patch_set]]}', flush=True)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Patched build failed: {error}\n')


if __name__ == '__main__':
    main()
