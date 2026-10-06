#!/usr/bin/env python3
"""Prepare and verify a larger LittleFS image from a device backup; never flash."""

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BLOCK_SIZE = 4096


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory(filesystem):
    result = {}
    for directory, _, names in filesystem.walk('/'):
        for name in names:
            path = directory.rstrip('/') + '/' + name
            with filesystem.open(path, 'rb') as source:
                content = source.read()
            result[path] = {'bytes': len(content), 'sha256': digest(content)}
    return result


def migration_seal(path):
    return re.fullmatch(r'/apps/[A-Za-z0-9][A-Za-z0-9._-]*/\.brookesia-verified\.json', path) is not None


def migrate(backup, output, size):
    from littlefs import LittleFS

    backup, output = Path(backup).resolve(), Path(output).resolve()
    if output.exists() or output == backup or ROOT in output.parents:
        raise ValueError('Output must be a new file outside the checkout')
    original = backup.read_bytes()
    if size <= len(original) or size % BLOCK_SIZE or size > 32 * 1024 * 1024:
        raise ValueError('Target must be a larger, block-aligned filesystem within 32 MiB')
    source = LittleFS(block_size=BLOCK_SIZE, block_count=0, mount=False)
    source.context.buffer = bytearray(original)
    source.mount()
    before = inventory(source)
    destination = LittleFS(block_size=BLOCK_SIZE, block_count=size // BLOCK_SIZE, name_max=64)
    invalidated = sorted(path for path in before if migration_seal(path))
    for directory, children, names in source.walk('/'):
        for child in children:
            destination.makedirs(directory.rstrip('/') + '/' + child, exist_ok=True)
        for name in names:
            path = directory.rstrip('/') + '/' + name
            if path in invalidated:
                continue
            with source.open(path, 'rb') as input_file, destination.open(path, 'wb') as output_file:
                while content := input_file.read(65536):
                    output_file.write(content)
    expected = {path: info for path, info in before.items() if path not in invalidated}
    after = inventory(destination)
    if after != expected:
        raise ValueError('Migrated file inventory or digest mismatch')
    free_bytes = (destination.block_count - destination.used_block_count) * BLOCK_SIZE
    destination.unmount()
    migrated = bytes(destination.context.buffer)
    check = LittleFS(block_size=BLOCK_SIZE, block_count=0, mount=False)
    check.context.buffer = bytearray(migrated)
    check.mount()
    if len(migrated) != size or check.block_count * BLOCK_SIZE != size or inventory(check) != expected:
        raise ValueError('Serialized filesystem did not preserve the verified inventory')
    if backup.read_bytes() != original:
        raise ValueError('Backup changed during migration')
    report = {
        'purpose': 'offline LittleFS expansion; Core must fully reverify migrated installations',
        'backup': str(backup), 'backupSha256': digest(original),
        'imageBytes': size, 'imageSha256': digest(migrated), 'freeBytes': free_bytes,
        'preservedFiles': len(after), 'invalidatedVerificationRecords': invalidated,
        'files': after,
    }
    report_path = output.with_suffix(output.suffix + '.json')
    if report_path.exists():
        raise ValueError('Migration report already exists')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as artifact:
        artifact.write(migrated)
    with report_path.open('x') as artifact:
        json.dump(report, artifact, indent=2)
        artifact.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--size', required=True, type=lambda value: int(value, 0))
    args = parser.parse_args()
    report = migrate(args.backup, args.output, args.size)
    print(f"Verified {report['preservedFiles']} preserved files; free {report['freeBytes']} bytes")
    print(f"Invalidated {len(report['invalidatedVerificationRecords'])} Core verification records")


if __name__ == '__main__':
    main()
