#!/usr/bin/env python3
"""Prepare public, test-only device inputs. Never copy a signing private key."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def prepare(inputs, output):
    inputs, output = Path(inputs), Path(output)
    if output.exists():
        raise ValueError('output must be new')
    payloads = {'public_key': (inputs / 'test-sign/public.pem').read_bytes()}
    for name, version in [('v1', '0.1.0'), ('v2', '0.2.0')]:
        payload = (inputs / f'espocket.test.store_hello.release.{version}.bpk').read_bytes()
        with zipfile.ZipFile(inputs / f'espocket.test.store_hello.release.{version}.bpk') as archive:
            manifest = json.loads(archive.read('manifest.json'))['package']
            if manifest['id'] != 'espocket.test.store_hello' or manifest['version'] != version or 'espocket' not in manifest['systems']:
                raise ValueError('unexpected test package identity')
            if not {'META-INF/hash.json', 'META-INF/signature.sig'} <= set(archive.namelist()):
                raise ValueError('test package must be signed')
        payloads[name] = payload
    output.mkdir(mode=0o700, parents=True)
    lines = ['#pragma once', '#include <cstdint>', 'namespace espocket::acceptance_inputs {']
    for name, data in payloads.items():
        lines.append(f'inline constexpr uint8_t {name}[] = {{' + ','.join(str(b) for b in data) + '};')
    lines.append('}')
    (output / 'package_acceptance_inputs.hpp').write_text('\n'.join(lines) + '\n')
    (output / 'report.json').write_text(json.dumps({'purpose': 'isolated-test-only',
        'privateKeyIncluded': False, 'published': False,
        'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}}, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.inputs, args.output)
