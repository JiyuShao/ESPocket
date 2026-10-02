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
    expected.pop('espressif/brookesia_runtime_js', None)
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
    registry = source / 'managed_components' / COMPONENT
    manifest = source / 'patches' / COMPONENT / VERSION / 'manifest.json'
    locked = json.loads(manifest.read_text())
    if locked['component'] != COMPONENT or locked['upstream_version'] != VERSION:
        raise ValueError('Unexpected patch identity')
    if inventory(registry) != locked['source_files']:
        raise ValueError('Locked source inventory/hash mismatch')
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
    patched = prepare(registry, manifest, workspace / 'patched_components' / COMPONENT)
    main_manifest = firmware / 'main/idf_component.yml'
    text = pin_registry_dependencies(main_manifest.read_text(), registry_lock(source / 'dependencies.lock'))
    original = f'  espressif/brookesia_runtime_js: "{VERSION}"\n'
    if text.count(original) != 1:
        raise ValueError('Main manifest no longer matches locked Runtime version')
    text = text.replace(original,
                        f'  espressif/brookesia_runtime_js:\n'
                        f'    version: "{VERSION}"\n'
                        f'    override_path: "../../patched_components/{COMPONENT}"\n')
    main_manifest.write_text(text)
    config = firmware / 'sdkconfig'
    lines = [line for line in config.read_text().splitlines()
             if 'CONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE' not in line]
    config.write_text('\n'.join(lines) + '\nCONFIG_BROOKESIA_RUNTIME_JS_ASYNC_STACK_SIZE=16384\n')
    (workspace / 'patch-inputs.json').write_text(json.dumps({
        'manifest_sha256': digest(manifest), 'source_files': locked['source_files'],
        'sdkconfig_input_sha256': digest(sdkconfig), 'async_stack_bytes': 16384,
        'original_registry_lock_sha256': digest(source / 'dependencies.lock'),
        'patched_component': str(patched), 'firmware_project': str(firmware),
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
            selected = description['build_component_info'][COMPONENT]['dir']
            expected = args.workspace.resolve() / 'patched_components' / COMPONENT
            if Path(selected).resolve() != expected:
                raise ValueError(f'Build selected unexpected Runtime source: {selected}')
            subprocess.run(['idf.py', '-C', str(firmware), 'build'], check=True)
            verify_registry_lock(ROOT / 'firmware/dependencies.lock', firmware / 'dependencies.lock')
            print(f'Verified selected patched Runtime: {selected}', flush=True)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Patched build failed: {error}\n')


if __name__ == '__main__':
    main()
