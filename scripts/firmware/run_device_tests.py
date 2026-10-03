#!/usr/bin/env python3
"""Run explicit device tests and retain one immutable attempt directory."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from firmware.test.device.support.device_test_runner import DeviceTestRunner, LIMITS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('navigation', 'cards', 'surfaces', 'apps', 'runtime-confirm', 'reclaim-native', 'reclaim-runtime', 'resources', 'settings-brightness'), default='navigation')
    parser.add_argument('--port', required=True)
    parser.add_argument('--device-id', required=True, help='board identity from inventory, not the serial port name')
    parser.add_argument('--expected-image', required=True, help='exact hello image_identity for this build')
    parser.add_argument('--profile', type=Path, default=ROOT / 'firmware/test/device/profiles/circular-466.json')
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/espocket-interaction'))
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text())
    directory = args.output.resolve() / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + str(uuid.uuid4()))
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / 'serial.log').open('xb') as raw_log:
        try:
            import serial  # Only the real USB CLI needs pyserial; host tests use an in-memory transport.
            with serial.Serial(args.port, 115200, timeout=0.05, write_timeout=1) as transport:
                report = DeviceTestRunner(transport, raw_log).attempt(
                    profile, device_id=args.device_id, expected_image=args.expected_image,
                    attempt_id=directory.name, suite=args.suite)
        except Exception as error:
            report = {'status': 'FAIL', 'attempt': directory.name, 'deviceId': args.device_id,
                      'expectedImage': args.expected_image, 'testSuite': args.suite, 'inputType': 'synthetic-input',
                      'physicalInputVerified': False, 'visualVerified': False, 'limitations': LIMITS,
                      'error': f'{type(error).__name__}: {error}', 'cleanup': 'transport unavailable'}
    report['port'] = args.port
    report['expectedImage'] = args.expected_image
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['status']}: {directory / 'report.json'}")
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
