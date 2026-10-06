"""Validate the product's built-in package inputs and exact staged bytes."""
import argparse
import json
from pathlib import Path


def require(root, member):
    path = (root / member).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing or invalid built-in resource: {root}/{member}')
    return path


def check_package(source, staged=None, runtime=False):
    resource = source / 'res'
    document = json.loads(require(resource, 'root.json').read_text())
    assets = document['assets'] + [asset for variant in document.get('variants', [])
                                   for asset in variant['assets']]
    for asset in assets:
        if isinstance(asset, str):
            path = require(resource, asset)
            data = json.loads(path.read_text())
            base = path.parent
        elif isinstance(asset, dict):
            # GUI roots also support inline assets (e.g. the 466px constants).
            data = asset
            base = resource
        else:
            raise ValueError(f'Invalid asset declaration: {asset}')
        if data.get('type') == 'imageSet':
            for image in data['images']:
                require(base, image['src'])
    if runtime:
        manifest = json.loads(require(source, 'manifest.json').read_text())
        require(source, manifest['runtime']['entry'])
        if manifest['runtime']['resource_dir'] != 'res':
            raise ValueError('Built-in Runtime resource directory no longer matches product staging')
        for member in ('profile.json', 'navigation.json', 'cards.json'):
            json.loads(require(resource, member).read_text())
    if staged is not None:
        inputs = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
        outputs = {p.relative_to(staged): p.read_bytes() for p in staged.rglob('*') if p.is_file()}
        if inputs != outputs:
            raise ValueError(f'Staged package differs from source: {staged}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--stage-root', type=Path)
    args = parser.parse_args()
    for name, source, runtime in (
        ('espocket.app.hello_runtime', args.runtime, True),
        ('brookesia.general.settings', args.settings, False),
        ('brookesia.general.app_store', args.store, False),
    ):
        check_package(source, args.stage_root / name if args.stage_root else None, runtime)
    print('Built-in package resource integrity passed.')


if __name__ == '__main__':
    main()
