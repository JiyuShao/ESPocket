#!/usr/bin/env python3
"""Prepare an explicit AEC trial in an existing isolated build; never flash."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from prepare_patched_component import prepare, inventory

ROOT = Path(__file__).resolve().parents[2]


def prepare_candidate(workspace, output, delay_ms):
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if workspace == ROOT or ROOT in workspace.parents or not (workspace / 'firmware/sdkconfig').is_file():
        raise ValueError('Requires an existing isolated firmware workspace outside the checkout')
    if output.exists() or ROOT in output.parents or not 0 <= delay_ms <= 250:
        raise ValueError('Requires a new external report and delay between 0 and 250 ms')
    component = 'espressif__brookesia_hal_adaptor'
    manifest = ROOT / 'firmware/patches' / component / '0.8.4/manifest.json'
    original_config = (workspace / 'firmware/sdkconfig').read_bytes()
    before = inventory(workspace / 'patched_components' / component)
    scratch = output.parent / (output.stem + '-hal')
    prepared = prepare(ROOT / 'firmware/managed_components' / component, manifest, scratch)
    shutil.copytree(prepared, workspace / 'patched_components' / component, dirs_exist_ok=True)
    after = inventory(workspace / 'patched_components' / component)
    if after != inventory(prepared):
        raise ValueError('Isolated HAL has stale or mismatched files')
    product = {}
    for relative in ('firmware/components/espocket_system', 'firmware/runtime_apps/ai_chatbot/src'):
        source, destination = ROOT / relative, workspace / relative
        shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__'))
        for artifact in source.rglob('*'):
            if artifact.is_file() and '__pycache__' not in artifact.parts:
                copied = destination / artifact.relative_to(source)
                if copied.read_bytes() != artifact.read_bytes():
                    raise ValueError('Product copy differs')
                product[artifact.relative_to(ROOT).as_posix()] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    config = original_config.decode()
    names = ('CONFIG_ESPOCKET_SOFTWARE_AEC_CANDIDATE', 'CONFIG_ESPOCKET_SOFTWARE_AEC_REFERENCE_DELAY_MS')
    lines = [line for line in config.splitlines() if not any(
        line.startswith(name + '=') or line == '# ' + name + ' is not set' for name in names)]
    config = '\n'.join(lines) + '\n' + names[0] + '=y\n' + names[1] + '=' + str(delay_ms) + '\n'
    (workspace / 'firmware/sdkconfig').write_text(config)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        'purpose': 'Uncalibrated software AEC trial; physical echo and interruption not verified; never deployed by this tool',
        'workspace': str(workspace), 'delayMs': delay_ms,
        'manifestSha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'halBefore': before, 'halAfter': after, 'productFiles': product,
        'sdkconfigBeforeSha256': hashlib.sha256(original_config).hexdigest(),
        'sdkconfigAfterSha256': hashlib.sha256(config.encode()).hexdigest(),
    }, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--delay-ms', type=int, default=0)
    args = parser.parse_args()
    prepare_candidate(args.workspace, args.report, args.delay_ms)
    print('Prepared isolated AEC candidate; device validation required')


if __name__ == '__main__':
    main()
