#!/usr/bin/env python3
"""Stage temporary Runtime isolation fixtures into a backed-up LittleFS image.

Offline test preparation, not a signed installation or publication path.
Run with the build's littlefs-python environment. Restore the input image
after the device gate; production firmware is unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'firmware/test/device/fixtures/keyboard_isolation'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(backup, output, token=None):
    from littlefs import LittleFS
    token = token or uuid.uuid4().hex
    if len(token) != 32 or any(c not in '0123456789abcdef' for c in token):
        raise ValueError('Fixture token must be a UUID hex string')
    backup, output = backup.resolve(), output.resolve()
    if output.exists() or output == backup or ROOT in output.parents:
        raise ValueError('Output must be a new image outside the checkout')
    original = backup.read_bytes()
    fs = LittleFS(block_size=4096, block_count=0, mount=False)
    fs.context.buffer = bytearray(original)
    fs.mount()

    def read(path):
        with fs.open(path, 'rb') as file:
            return file.read()

    def inventory():
        return {path.rstrip('/') + '/' + name: digest(read(path.rstrip('/') + '/' + name))
                for path, _, names in fs.walk('/') for name in names}

    def write(path, data):
        fs.makedirs(path.rsplit('/', 1)[0], exist_ok=True)
        with fs.open(path, 'wb') as file:
            file.write(data)

    before = inventory()
    owner = '/apps/espocket.app.hello_runtime'
    manifest = json.loads(read(owner + '/manifest.json'))
    if manifest['package']['id'] != 'espocket.app.hello_runtime':
        raise ValueError('Unexpected reference package identity')
    # Explicit fixture-only requirement; preserve Core's declared-service gate.
    manifest['services'] = [{'name': 'Display', 'version': '0.8.2'}]
    observers = ['espocket.test.keyboard.' + token + '.' + role for role in ('normal', 'failed')]
    for index, app_id in enumerate(observers):
        base = '/apps/' + app_id
        if any(path == base or path.startswith(base + '/') for path in before):
            raise ValueError('Refusing to overwrite unknown fixture directory')
        copied = json.loads(json.dumps(manifest))
        copied['package'].update(id=app_id, visible=False, name={'en': 'Keyboard isolation fixture'})
        write(base + '/manifest.json', json.dumps(copied).encode())
        write(base + '/res/profile.json', b'{}')
        prefix = 'globalThis.keyboardIsolation = ' + json.dumps({'failStop': index == 1}) + ';\n'
        write(base + '/app/main.js', (prefix + (FIXTURES / 'observer.js').read_text()).encode())
    write(owner + '/manifest.json', json.dumps(manifest).encode())
    write(owner + '/app/main.js', (FIXTURES / 'owner.js').read_bytes())
    after = inventory()
    changed = {path: {'before': before.get(path), 'after': value}
               for path, value in after.items() if before.get(path) != value}
    assert all(path in (owner + '/app/main.js', owner + '/manifest.json') or
               any(path.startswith('/apps/' + app + '/') for app in observers) for path in changed)
    assert before.keys() <= after.keys(), 'Preparation removed an existing file'
    fs.unmount()
    output.write_bytes(fs.context.buffer)
    assert output.stat().st_size == len(original)
    ledger = {'purpose': 'temporary true Runtime keyboard isolation gate; restore backup afterward',
              'backup': str(backup), 'backupSha256': digest(original),
              'imageSha256': digest(output.read_bytes()), 'observers': observers,
              'changedFiles': changed, 'preservedFiles': len(before) - 2}
    output.with_suffix('.json').write_text(json.dumps(ledger, indent=2) + '\n')
    return ledger


def prepare_coordinator(project, ledger):
    """Add Native orchestration only to an isolated test project."""
    project = project.resolve()
    if project == ROOT or ROOT in project.parents or project in ROOT.parents:
        raise ValueError('Coordinator project must be outside the checkout')
    relative = Path('components/espocket_system/src/system_power.cpp')
    source = project / relative
    original = (ROOT / 'firmware' / relative).read_text()
    if source.read_text() != original:
        raise ValueError('Coordinator seam must match the uninstrumented checkout')
    header = source.parent / 'keyboard_isolation_coordinator.hpp'
    if header.exists():
        raise ValueError('Coordinator already present')
    template = (FIXTURES / 'coordinator.hpp').read_text()
    text = template.replace('KISO_NORMAL_ID', ledger['observers'][0]).replace('KISO_FAILED_ID', ledger['observers'][1])
    include = '#include "system_internal.hpp"'
    tick = '    drain_runtime_navigation();'
    if original.count(include) != 1 or original.count(tick) != 1:
        raise ValueError('Unexpected serialized Native input seam')
    header.write_text(text)
    source.write_text(original.replace(include, include + '\n#include "keyboard_isolation_coordinator.hpp"')
                      .replace(tick, '    keyboard_isolation::poll(*this);\n' + tick))
    (project.parent / 'keyboard-isolation-inputs.json').write_text(json.dumps({
        'purpose': 'temporary Native coordinator; original Runtime permissions unchanged',
        'project': str(project), 'observers': ledger['observers'],
        'coordinatorSha256': digest(header.read_bytes()),
        'sourceBeforeSha256': digest(original.encode()), 'sourceAfterSha256': digest(source.read_bytes()),
    }, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--project', type=Path,
                        help='optional isolated product build; add explicit Native coordinator before building')
    args = parser.parse_args()
    result = prepare(args.backup, args.output)
    if args.project:
        prepare_coordinator(args.project, result)
    print('Prepared', len(result['changedFiles']), 'temporary fixture files; unrelated files preserved')
