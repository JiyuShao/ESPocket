#!/usr/bin/env python3
"""Run the explicitly staged true Runtime keyboard fixture through USB input.

Requires Developer Mode and prepare_keyboard_isolation_fixture.py's image.
Never flashes, modifies developer settings, or disables keyboard containment.
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from firmware.test.device.support.device_test_runner import DeviceTestRunner
from firmware.test.device.e2e.keyboard_isolation import run


if __name__ == '__main__':
    import serial
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--expected-image', required=True)
    parser.add_argument('--device-id', required=True, help='explicit device inventory identity')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / 'serial.log'
    report = {'status': 'RUNNING', 'expectedImage': args.expected_image, 'deviceId': args.device_id,
              'limits': 'Synthetic input; no real user text, signed installation, or physical touch claim.'}
    runner = None
    try:
        with serial.Serial(args.port, 115200, timeout=.05) as port, path.open('wb') as log:
            port.write(b'\n')
            time.sleep(.2)
            port.reset_input_buffer()
            runner = DeviceTestRunner(port, log)
            report['identity'] = runner.hello(args.expected_image)
            try:
                profile = json.loads((ROOT / 'firmware/test/device/profiles/circular-466.json').read_text())
                run(runner, path, profile)
                report['status'] = 'PASS'
            finally:
                runner.request('release')
    except Exception as error:
        report.update(status='FAIL', error=str(error))
    finally:
        report['steps'] = runner.steps if runner else []
        (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'], args.output / 'report.json')
    sys.exit(0 if report['status'] == 'PASS' else 1)
