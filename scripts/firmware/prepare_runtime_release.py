#!/usr/bin/env python3
"""Build and verify a release with an explicitly supplied publisher key; never publish."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]

def prepare(source, signing_directory, output, artifact_url, node='node'):
    source, signing_directory, output = (Path(p).resolve() for p in (source, signing_directory, output))
    if output.exists(): raise ValueError('output must be new')
    if not artifact_url.startswith('https://'): raise ValueError('artifact URL must use HTTPS')
    for name in ('private.pem', 'public.pem'):
        if not (signing_directory / name).is_file(): raise ValueError('publisher signing directory must contain existing private.pem and public.pem')
    manifest = json.loads((source / 'manifest.json').read_text())['package']
    if 'espocket' not in manifest.get('systems', []): raise ValueError('release must explicitly support espocket')
    package_id, version = manifest['id'], manifest['version']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', package_id): raise ValueError('invalid package identity')
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', version): raise ValueError('invalid package version')
    sdk = ROOT / 'firmware/runtime_apps/hello/node_modules/@brookesia/packager'
    installed = json.loads((sdk / 'package.json').read_text())
    locked = json.loads((ROOT / 'firmware/runtime_apps/hello/package-lock.json').read_text())['packages']['node_modules/@brookesia/packager']
    if installed['version'] != locked['version']: raise ValueError('packager does not match lock')
    output.mkdir(parents=True, mode=0o700)
    artifact = output / f'{package_id}.{version}.release.bpk'
    operation = {'sourceDir': str(source), 'outputPath': str(artifact), 'mode': 'production', 'signDir': str(signing_directory)}
    script = '''const {packAppPackage,verifyPackage}=await import(process.argv[1]);
const operation=JSON.parse(process.argv[2]);
const file=await packAppPackage(operation);
await verifyPackage(file,operation.signDir+'/public.pem');'''
    subprocess.run([node, '--input-type=module', '-e', script, (sdk / 'dist/index.mjs').as_uri(), json.dumps(operation)], check=True)
    with zipfile.ZipFile(artifact) as archive:
        if not {'META-INF/hash.json', 'META-INF/signature.sig'} <= set(archive.namelist()): raise ValueError('missing signature')
        stored = json.loads(archive.read('manifest.json'))['package']
        if stored['id'] != package_id or stored['version'] != version: raise ValueError('artifact identity mismatch')
        uncompressed = sum(info.file_size for info in archive.infolist())
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    metadata = {'package_name': package_id, 'version': version, 'bpk_type': 'jsbundle',
                'size_download': artifact.stat().st_size, 'size_uncompressed': uncompressed,
                'hash_sha256': digest, 'download_url': artifact_url}
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    report = {'artifact': artifact.name, 'artifactSha256': digest, 'publisherPublicKeySha256':
              hashlib.sha256((signing_directory / 'public.pem').read_bytes()).hexdigest(),
              'packagerVersion': installed['version'], 'sdkSignatureVerified': True,
              'published': False, 'deviceAccepted': False,
              'limitations': 'Key ownership, catalog authorization, target URL content and Core device acceptance require separate evidence.'}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--sign-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-url', required=True)
    parser.add_argument('--node', default='node')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.sign_dir, args.output, args.artifact_url, args.node)))
