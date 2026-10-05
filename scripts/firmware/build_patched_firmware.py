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
    'production': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3'), ('espressif__brookesia_service_display', '0.8.2'), ('espressif__esp_board_manager', '0.5.15'), ('espressif__brookesia_app_store', '0.8.2'), ('espressif__brookesia_lib_utils', '0.8.2'), ('espressif__brookesia_service_storage', '0.8.3')),
    'hal-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'),),
    'audio-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3')),
    'display-candidate': PATCHES + (('espressif__brookesia_hal_adaptor', '0.8.4'), ('espressif__brookesia_app_settings', '0.8.3'), ('espressif__brookesia_service_display', '0.8.2')),
}

# Keep the explicit candidate entry for reproducible historical commands.
PATCH_SETS['store-candidate'] = PATCH_SETS['production']


AUDIO_OPTIONS = {
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


def audio_dependencies(root):
    path = root / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/audio-candidate-dependencies.json'
    document = json.loads(path.read_text())
    if document['schema_version'] != 1:
        raise ValueError('Unknown audio candidate dependency schema')
    return document['dependencies']


def configure_audio_candidate(text):
    lines = [line for line in text.splitlines() if not any(
        line.startswith(key + '=') or line.startswith('# ' + key + ' ')
        for key in AUDIO_OPTIONS)]
    for key, enabled in AUDIO_OPTIONS.items():
        if type(enabled) is bool:
            lines.append(key + '=y' if enabled else '# ' + key + ' is not set')
        else:
            lines.append(key + '=' + str(enabled))
    return '\n'.join(lines) + '\n'


def verify_audio_config(text):
    for key, enabled in AUDIO_OPTIONS.items():
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
    if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate'):
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


def stage(root, workspace, sdkconfig, patch_set='production'):
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
        manifest = source / 'patches' / component / version / 'manifest.json'
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
    shutil.copyfile(sdkconfig, firmware / 'sdkconfig')
    main_manifest = firmware / 'main/idf_component.yml'
    constraints = registry_lock(source / 'dependencies.lock')
    audio_extra = audio_dependencies(root) if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate') else {}
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
                             'manifest_sha256': digest(manifest), 'source_files': locked['source_files'],
                             'patched_component': str(patched)})
    main_manifest.write_text(text)
    config = firmware / 'sdkconfig'
    if patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate'):
        config.write_text(configure_audio_candidate(config.read_text()))
    lines = [line for line in config.read_text().splitlines()
             if 'CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE' not in line]
    config.write_text('\n'.join(lines) + '\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=16384\n')
    (workspace / 'patch-inputs.json').write_text(json.dumps({
        'patch_set': patch_set,
        'audio_candidate_dependencies': audio_extra,
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
    args = parser.parse_args()
    try:
        firmware = stage(ROOT, args.workspace, args.sdkconfig.resolve(), args.patch_set)
        print(f'Prepared firmware: {firmware}', flush=True)
        if not args.prepare_only:
            subprocess.run(['idf.py', '-C', str(firmware), 'reconfigure'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock', args.patch_set)
            if args.patch_set in ('production', 'audio-candidate', 'display-candidate', 'store-candidate'):
                verify_audio_config((firmware / 'sdkconfig').read_text())
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
