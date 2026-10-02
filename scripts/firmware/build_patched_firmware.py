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

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = 'espressif__brookesia_runtime_js'
VERSION = '0.8.3'
PATCHES = ((COMPONENT, VERSION), ('espressif__brookesia_system_core', '0.8.4'))


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


def verify_registry_lock(original, generated):
    expected = registry_lock(original)
    actual = registry_lock(generated)
    for component, _ in PATCHES:
        expected.pop(component.replace('__', '/'), None)
    if actual != expected:
        changed = sorted(name for name in set(actual) | set(expected)
                         if actual.get(name) != expected.get(name))
        raise ValueError(f'Unexpected registry dependency drift: {changed}')


def stage(root, workspace, sdkconfig):
    root = root.resolve()
    source = root / 'firmware'
    workspace = workspace.resolve()
    if workspace.exists():
        raise ValueError('Workspace must be new; preserve previous build evidence')
    if workspace == root or root in workspace.parents or workspace in root.parents:
        raise ValueError('Workspace must be outside the source checkout')
    manifests = []
    for component, version in PATCHES:
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
    text = pin_registry_dependencies(main_manifest.read_text(), registry_lock(source / 'dependencies.lock'))
    patch_inputs = []
    for component, version, registry, manifest, locked in manifests:
        patched = prepare(registry, manifest, workspace / 'patched_components' / component)
        dependency = component.replace('__', '/')
        original = f'  {dependency}: "{version}"\n'
        if text.count(original) != 1:
            raise ValueError(f'Main manifest no longer matches locked patch version: {dependency}')
        text = text.replace(original,
                            f'  {dependency}:\n'
                            f'    version: "{version}"\n'
                            f'    override_path: "../../patched_components/{component}"\n')
        patch_inputs.append({'component': component, 'version': version,
                             'manifest_sha256': digest(manifest), 'source_files': locked['source_files'],
                             'patched_component': str(patched)})
    main_manifest.write_text(text)
    config = firmware / 'sdkconfig'
    lines = [line for line in config.read_text().splitlines()
             if 'CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE' not in line]
    config.write_text('\n'.join(lines) + '\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=16384\n')
    (workspace / 'patch-inputs.json').write_text(json.dumps({
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
                        help='existing board-configured sdkconfig; copied without modification')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    try:
        firmware = stage(ROOT, args.workspace, args.sdkconfig.resolve())
        print(f'Prepared firmware: {firmware}', flush=True)
        if not args.prepare_only:
            subprocess.run(['idf.py', '-C', str(firmware), 'reconfigure'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock')
            description = json.loads((firmware / 'build/project_description.json').read_text())
            for component, _ in PATCHES:
                selected = description['build_component_info'][component]['dir']
                expected = args.workspace.resolve() / 'patched_components' / component
                if Path(selected).resolve() != expected:
                    raise ValueError(f'Build selected unexpected patched source: {selected}')
            subprocess.run(['idf.py', '-C', str(firmware), 'build'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock')
            print(f'Verified patched components: {[item[0] for item in PATCHES]}', flush=True)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Patched build failed: {error}\n')


if __name__ == '__main__':
    main()
