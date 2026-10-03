#!/usr/bin/env python3
"""Prepare isolated signed Store test artifacts using the locked official SDK.

The generated ephemeral key is a test identity, never a production trust root.
No artifact is published or installed by this command.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
APP_ID = 'espocket.test.store_hello'


def prepare(output, node):
    output = output.resolve()
    if output.exists():
        raise ValueError('Output must be new; preserve prior artifact evidence')
    if output == ROOT or ROOT in output.parents or output in ROOT.parents:
        raise ValueError('Output must be outside the checkout')
    sdk = ROOT / 'firmware/runtime_apps/hello/node_modules/@brookesia/packager'
    identity = json.loads((sdk / 'package.json').read_text())
    locked = json.loads((ROOT / 'firmware/runtime_apps/hello/package-lock.json').read_text())['packages']['node_modules/@brookesia/packager']
    if identity['version'] != locked['version']:
        raise ValueError('Installed packager version differs from package-lock')
    module = sdk / 'dist/index.mjs'
    output.mkdir(parents=True)
    operations = []
    for version in ('0.1.0', '0.2.0'):
        source = output / 'source' / version
        shutil.copytree(ROOT / 'firmware/runtime_apps/hello/src', source)
        for path in source.rglob('*.json'):
            text = path.read_text().replace('espocket.app.hello_runtime', APP_ID).replace('0.1.0', version)
            path.write_text(text)
        manifest = json.loads((source / 'manifest.json').read_text())
        manifest['package']['name'] = {'en': 'Store Test Hello'}
        (source / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        operations.append({'sourceDir': str(source), 'outputPath': str(output / f'{APP_ID}.release.{version}.bpk'),
                           'mode': 'production', 'signDir': str(output / 'test-sign')})
    script = '''const {packAppPackage,verifyPackage}=await import(process.argv[1]);
for(const operation of JSON.parse(process.argv[2])){
 const file=await packAppPackage(operation);
 await verifyPackage(file,operation.signDir+'/public.pem');
}
'''
    subprocess.run([node, '--input-type=module', '-e', script, module.as_uri(), json.dumps(operations)], check=True)
    packages = []
    for file in sorted(output.glob('*.bpk')):
        with zipfile.ZipFile(file) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            assert manifest['package']['systems'] == ['espocket']
            assert {'META-INF/hash.json', 'META-INF/signature.sig'} <= set(archive.namelist())
        packages.append({'file': file.name, 'id': APP_ID, 'version': manifest['package']['version'],
                         'artifactSha256': hashlib.sha256(file.read_bytes()).hexdigest(), 'size': file.stat().st_size})
    public_key = output / 'test-sign/public.pem'
    report = {'purpose': 'isolated-test-only', 'installed': False, 'published': False,
              'productionTrustRoot': False, 'sdk': {'name': identity['name'], 'version': identity['version'],
              'lockIntegrity': locked['integrity'], 'moduleSha256': hashlib.sha256(module.read_bytes()).hexdigest()},
              'testPublicKeySha256': hashlib.sha256(public_key.read_bytes()).hexdigest(), 'packages': packages,
              'limitations': 'SDK verification does not prove Core install/discovery, receipts, rollback or catalog publication.'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    prepare(args.output, args.node)
    print(f'Prepared isolated test releases: {args.output / "report.json"}')
