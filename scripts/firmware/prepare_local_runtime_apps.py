#!/usr/bin/env python3
"""Pack maintained local Runtime Apps with the locked official SDK; never deploy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
APPS = ('ai_chatbot', 'calculator')


def prepare(name, output=None, node='node'):
    if name not in APPS:
        raise ValueError('Unknown maintained local App')
    source = ROOT / 'firmware/runtime_apps' / name / 'src'
    manifest = json.loads((source / 'manifest.json').read_text())['package']
    if manifest['id'] != f'espocket.app.{name}' or manifest['systems'] != ['espocket']:
        raise ValueError('Local package identity or system declaration changed')
    sdk = ROOT / 'firmware/runtime_apps/hello/node_modules/@brookesia/packager'
    locked = json.loads((ROOT / 'firmware/runtime_apps/hello/package-lock.json').read_text())
    version = json.loads((sdk / 'package.json').read_text())['version']
    if version != locked['packages']['node_modules/@brookesia/packager']['version']:
        raise ValueError('Packager does not match the SDK lock')
    output = Path(output).resolve() if output else source.parent / 'dist'
    if output == source or source in output.parents:
        raise ValueError('Output must be outside the package source')
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / f"{manifest['id']}.debug.{manifest['version']}.bpk"
    operation = {'sourceDir': str(source), 'outputPath': str(artifact), 'mode': 'development'}
    script = 'const {packAppPackage}=await import(process.argv[1]);await packAppPackage(JSON.parse(process.argv[2]));'
    subprocess.run([node, '--input-type=module', '-e', script, (sdk / 'dist/index.mjs').as_uri(),
                    json.dumps(operation)], check=True)
    expected = {path.relative_to(source).as_posix(): path.read_bytes()
                for path in source.rglob('*') if path.is_file()}
    with zipfile.ZipFile(artifact) as archive:
        if archive.testzip() is not None:
            raise ValueError('BPK CRC verification failed')
        members = [item.filename for item in archive.infolist() if not item.is_dir()]
        if len(members) != len(set(members)) or {name: archive.read(name) for name in members} != expected:
            raise ValueError('BPK members differ from maintained source')
    report = {'id': manifest['id'], 'version': manifest['version'], 'artifact': str(artifact),
              'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(), 'bytes': artifact.stat().st_size,
              'members': len(expected), 'packagerVersion': version, 'sourceVerified': True,
              'signed': False, 'deviceAccepted': False}
    (output / 'package-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', choices=APPS, action='append')
    parser.add_argument('--output', type=Path, help='output root; each App gets its own subdirectory')
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    for name in args.app or APPS:
        print(json.dumps(prepare(name, args.output / name if args.output else None, args.node)))


if __name__ == '__main__':
    main()
