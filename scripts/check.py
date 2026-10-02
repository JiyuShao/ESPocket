#!/usr/bin/env python3
"""Run read-only host checks; firmware builds and hardware checks are separate."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagrams', action='store_true',
                        help='also check architecture diagrams (requires Node and Chrome)')
    args = parser.parse_args()
    commands = [
        ('Markdown', [sys.executable, '-B', 'scripts/docs/check.py', '--markdown']),
        ('Lifecycle parser', [sys.executable, '-B',
                              'scripts/firmware/verify_m2_lifecycle.py', '--self-test']),
    ]
    test_directories = sorted((ROOT / 'firmware/components').glob('*/test'))
    test_directories += sorted((ROOT / 'firmware/native_apps').glob('*/test'))
    test_directories += sorted((ROOT / 'firmware/runtime_apps').glob('*/test'))
    test_directories.append(ROOT / 'firmware/test/host')
    for directory in test_directories:
        commands.append((str(directory.relative_to(ROOT)), [
            sys.executable, '-B', '-m', 'unittest', 'discover',
            '-s', str(directory), '-p', 'test_*.py',
        ]))
    if args.diagrams:
        commands.append(('Architecture diagrams', [sys.executable, '-B',
                                                   'scripts/docs/check.py', '--diagrams']))
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    failed = []
    for name, command in commands:
        print(f'Checking {name}', flush=True)
        if subprocess.run(command, cwd=ROOT, env=environment).returncode:
            failed.append(name)
    if failed:
        print('Failed: ' + ', '.join(failed), file=sys.stderr)
        return 1
    print('All host checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
