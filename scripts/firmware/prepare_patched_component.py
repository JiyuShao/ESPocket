#!/usr/bin/env python3
"""Verify and patch a locked component into a new, separate build directory."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(value):
    path = Path(value)
    if path.is_absolute() or not path.parts or '..' in path.parts:
        raise ValueError(f'Unsafe relative path: {value}')
    return path


def inventory(directory):
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlink not supported: {path}')
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = digest(path)
    return result


def apply_exact_patch(directory, patch):
    """Accept text modifications only; hunk coordinates and context must match exactly."""
    lines = patch.read_text().splitlines(keepends=True)
    cursor = 0
    seen = set()
    while cursor < len(lines):
        if not lines[cursor].startswith('--- a/') or cursor + 1 >= len(lines):
            raise ValueError('Expected unified patch file header')
        old_name = lines[cursor][6:].rstrip('\n')
        new_header = lines[cursor + 1]
        if new_header != f'+++ b/{old_name}\n' or old_name in seen:
            raise ValueError('Renames, duplicate files and file creation are unsupported')
        seen.add(old_name)
        target = directory / relative_path(old_name)
        original = target.read_text().splitlines(keepends=True)
        output = []
        consumed = 0
        cursor += 2
        hunks = 0
        while cursor < len(lines) and lines[cursor].startswith('@@ '):
            match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n', lines[cursor])
            if not match:
                raise ValueError('Invalid hunk header')
            old_start, old_count, new_start, new_count = match.groups()
            start = int(old_start) - 1
            if start < consumed or start > len(original):
                raise ValueError('Invalid or overlapping hunk coordinates')
            output.extend(original[consumed:start])
            if int(new_start) != len(output) + 1:
                raise ValueError('New hunk coordinate mismatch')
            consumed = start
            cursor += 1
            removed = added = 0
            while cursor < len(lines) and lines[cursor][:1] in (' ', '+', '-'):
                if lines[cursor].startswith('--- a/'):
                    break
                kind, content = lines[cursor][0], lines[cursor][1:]
                if kind in (' ', '-'):
                    if consumed >= len(original) or original[consumed] != content:
                        raise ValueError(f'Exact patch context mismatch: {old_name}:{consumed + 1}')
                    consumed += 1
                    removed += 1
                if kind in (' ', '+'):
                    output.append(content)
                    added += 1
                cursor += 1
            if removed != int(old_count or 1) or added != int(new_count or 1):
                raise ValueError('Hunk length mismatch')
            hunks += 1
        if not hunks:
            raise ValueError('File patch has no hunks')
        output.extend(original[consumed:])
        target.write_text(''.join(output))
    if not seen:
        raise ValueError('Empty patch')


def prepare(source, manifest_path, output):
    source, output = source.resolve(), output.resolve()
    if 'managed_components' in output.parts:
        raise ValueError('Output cannot be inside managed_components')
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('Output must be separate from the source component')
    if output.exists():
        raise ValueError('Output already exists; use a new build directory')
    manifest = json.loads(manifest_path.read_text())
    if manifest['schema_version'] != 1:
        raise ValueError('Unsupported manifest schema')
    # Hash every file, including component metadata. A copied hash marker alone is insufficient.
    if inventory(source) != manifest['source_files']:
        raise ValueError('Locked source inventory/hash mismatch')
    patches = []
    for entry in manifest['patches']:
        path = manifest_path.parent / relative_path(entry['file'])
        if digest(path) != entry['sha256']:
            raise ValueError(f'Patch hash mismatch: {path.name}')
        patches.append(path)
    if not patches:
        raise ValueError('No patches declared')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.patch-stage-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'component'
        shutil.copytree(source, staged)
        # Check the copy too, so concurrent source changes cannot escape validation.
        if inventory(staged) != manifest['source_files']:
            raise ValueError('Source changed while copying')
        for patch in patches:
            apply_exact_patch(staged, patch)
        staged.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(prepare(args.source, args.manifest, args.output))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'Component preparation failed: {error}\n')


if __name__ == '__main__':
    main()
