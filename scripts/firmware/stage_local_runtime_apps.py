#!/usr/bin/env python3
"""Stage exact built-in App sources into a backed-up LittleFS image; never flash.

This prepares product-image inputs, not dynamic Core installation receipts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from migrate_littlefs import inventory

ROOT = Path(__file__).resolve().parents[2]
APPS = ('ai_chatbot', 'calculator')
BLOCK_SIZE = 4096


def stage(backup, output, filesystem_only=False, update_builtins=False):
    from littlefs import LittleFS

    backup, output = Path(backup).resolve(), Path(output).resolve()
    if output.exists() or output.with_suffix(output.suffix + '.json').exists():
        raise ValueError('Output and report must be new')
    original = backup.read_bytes()
    if filesystem_only:
        image = original
    else:
        if len(original) != 0x2000000:
            raise ValueError('Expected a complete 32 MiB device backup')
        partitions = []
        for offset in range(0x8000, 0x8000 + 0x1000, 32):
            magic, kind, subtype, address, size, label, flags = struct.unpack_from('<HBBII16sI', original, offset)
            if magic != 0x50AA:
                break
            if label.rstrip(b'\0') == b'littlefs_data':
                partitions.append((address, size))
        if partitions != [(0xe60000, 0x11a0000)]:
            raise ValueError('Device LittleFS partition differs from the product layout')
        address, size = partitions[0]
        image = original[address:address + size]
    filesystem = LittleFS(block_size=BLOCK_SIZE, block_count=0, mount=False)
    filesystem.context.buffer = bytearray(image)
    filesystem.mount()
    before = inventory(filesystem)
    expected = dict(before)
    reports = []
    for name in APPS:
        local_id, old_id = f'espocket.app.{name}', f'brookesia.general.{name}'
        source = ROOT / 'firmware/runtime_apps' / name / 'src'
        manifest = json.loads((source / 'manifest.json').read_text())['package']
        if manifest['id'] != local_id or manifest['systems'] != ['espocket']:
            raise ValueError('Unexpected built-in identity')
        destination = f'/apps/{local_id}'
        installed = {path: info for path, info in before.items() if path.startswith(destination + '/')}
        invalidated = []
        if installed:
            if not update_builtins:
                raise ValueError('Local App already exists; use --update-builtins for product-image updates')
            with filesystem.open(destination + '/manifest.json', 'r') as artifact:
                previous = json.loads(artifact.read())['package']
            if previous['id'] != local_id or previous['systems'] != ['espocket']:
                raise ValueError('Installed App is not the maintained product identity')
            # A dynamically installed package must use Core's installer, not image staging.
            if any(destination + '/' + member in installed for member in (
                    '.brookesia-install.json', '.brookesia-install.pending', '.brookesia-package.bpk')):
                raise ValueError('Dynamic installation cannot be replaced as a built-in')
            for path in installed:
                relative = path[len(destination) + 1:]
                if relative.split('/')[0] in ('data', 'files', 'cache'):
                    continue
                filesystem.remove(path)
                expected.pop(path)
                if relative.startswith('.brookesia-'):
                    invalidated.append(relative)
        files = {path.relative_to(source).as_posix(): path.read_bytes()
                 for path in source.rglob('*') if path.is_file()}
        migrated = []
        for path in (() if installed else before):
            prefix = f'/apps/{old_id}/'
            if path.startswith(prefix) and path[len(prefix):].split('/')[0] in ('data', 'files'):
                relative = path[len(prefix):]
                with filesystem.open(path, 'rb') as artifact:
                    files[relative] = artifact.read()
                migrated.append(relative)
        for relative, content in files.items():
            path = destination + '/' + relative
            if installed and relative.split('/')[0] in ('data', 'files', 'cache') and path in before:
                continue  # Existing private content wins over package seed defaults.
            filesystem.makedirs(str(Path(path).parent), exist_ok=True)
            with filesystem.open(path, 'wb') as artifact:
                artifact.write(content)
            expected[path] = {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
        reports.append({'id': local_id, 'version': manifest['version'], 'members': len(files),
                        'migratedPrivateMembers': migrated, 'oldInstallationPreserved': True,
                        'updatedBuiltin': bool(installed), 'invalidatedVerificationRecords': invalidated})
    if inventory(filesystem) != expected:
        raise ValueError('Staging changed unrelated files or failed to preserve private data')
    filesystem.unmount()
    result = bytes(filesystem.context.buffer)
    check = LittleFS(block_size=BLOCK_SIZE, block_count=0, mount=False)
    check.context.buffer = bytearray(result)
    check.mount()
    if inventory(check) != expected:
        raise ValueError('Serialized image differs from the verified inventory')
    report = {'backupSha256': hashlib.sha256(original).hexdigest(),
              'imageSha256': hashlib.sha256(result).hexdigest(), 'imageBytes': len(result),
              'preservedFiles': len(before), 'apps': reports,
              'unrelatedFilesPreserved': True, 'oldInstallationsRemoved': False,
              'files': expected}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as artifact:
        artifact.write(result)
    output.with_suffix(output.suffix + '.json').write_text(json.dumps(report, indent=2) + '\n')
    return {key: value for key, value in report.items() if key != 'files'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--filesystem-only', action='store_true')
    parser.add_argument('--update-builtins', action='store_true',
                        help='replace maintained built-in code while preserving private and unrelated files')
    args = parser.parse_args()
    print(json.dumps(stage(args.backup, args.output, args.filesystem_only, args.update_builtins)))


if __name__ == '__main__':
    main()
