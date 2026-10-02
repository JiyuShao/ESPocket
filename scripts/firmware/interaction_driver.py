#!/usr/bin/env python3
"""Run USB synthetic-input checks and retain one immutable attempt directory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import time
import uuid

PREFIX = b'@ESPTEST '
VERSION = 1
CAPABILITIES = {'hello', 'snapshot', 'stimulus.touch', 'stimulus.powerShort', 'release'}
LIMITS = 'Synthetic input does not verify touch hardware, PWR GPIO, or visual feedback.'


class DriverError(RuntimeError):
    pass


class Driver:
    def __init__(self, transport, raw_log, *, clock=time.monotonic, sleep=time.sleep,
                 timeout=3.0, request_seed=None):
        self.transport = transport
        self.raw_log = raw_log
        self.clock = clock
        self.sleep = sleep
        self.timeout = timeout
        self.request_id = request_seed if request_seed is not None else secrets.randbits(32) << 16
        self.last_seq = 0
        self.snapshots = []
        self.steps = []
        self.identity = None
        self.attempt_started = False

    def request(self, op, **parameters):
        self.request_id += 1
        request = {'version': VERSION, 'request_id': self.request_id, 'op': op, **parameters}
        frame = PREFIX + json.dumps(request, separators=(',', ':')).encode() + b'\n'
        if len(frame.rstrip(b'\n')) > 1024:
            raise DriverError('request exceeds firmware frame limit')
        self.raw_log.write(b'TX ' + frame)
        self.raw_log.flush()
        if self.transport.write(frame) != len(frame):
            raise DriverError('partial request write')
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            line = self.transport.readline(4096)
            if not line:
                continue
            self.raw_log.write(b'RX ' + line)
            self.raw_log.flush()
            if not line.startswith(PREFIX):
                self.check_log(line)
                continue
            try:
                reply = json.loads(line[len(PREFIX):])
            except (ValueError, UnicodeDecodeError) as error:
                raise DriverError('malformed protocol response') from error
            if not isinstance(reply, dict):
                raise DriverError('response must be an object')
            if reply.get('request_id') != self.request_id:
                # Old serial responses cannot satisfy this attempt's fresh request.
                continue
            if reply.get('version') != VERSION or type(reply.get('ok')) is not bool:
                raise DriverError('invalid response envelope')
            if not reply['ok']:
                raise DriverError(f"{op}: {reply.get('error_code', 'missing error code')}")
            return reply
        raise DriverError(f'{op}: response timeout')

    @staticmethod
    def check_log(line):
        markers = (b'A stack overflow in task', b'Guru Meditation', b'panic_abort', b'abort() was called', b'ESP_RST_PANIC',
                   b'Synthetic input tick failed:', b'Input cleanup during stop failed:',
                   b'Synthetic PWR expired', b'Synthetic PWR cancelled',
                   b'USB Test Adapter response write failed', b'ESP-ROM:esp32', b'ESPocket started')
        if any(marker in line for marker in markers):
            raise DriverError('device error observed; see serial.log')

    def hello(self, expected_image=None):
        reply = self.request('hello')
        identity = reply.get('image_identity')
        capabilities = reply.get('capabilities')
        if not isinstance(identity, str) or not identity or not isinstance(capabilities, list) or \
                any(not isinstance(item, str) for item in capabilities):
            raise DriverError('invalid hello identity/capabilities')
        self.identity = {'image_identity': identity, 'protocol_version': VERSION,
                         'capabilities': capabilities}
        if expected_image is not None and identity != expected_image:
            raise DriverError(f'image mismatch: expected {expected_image}, received {identity}')
        if not CAPABILITIES.issubset(capabilities):
            raise DriverError('firmware lacks required capabilities; do not infer support from source')
        return self.identity

    def snapshot(self):
        value = self.request('snapshot').get('snapshot')
        if not isinstance(value, dict):
            raise DriverError('missing snapshot')
        if type(value.get('seq')) is not int or value['seq'] <= self.last_seq:
            raise DriverError('snapshot sequence did not advance; possible device/Adapter restart')
        for field in ('display', 'canBack', 'backPending', 'inputBusy'):
            if type(value.get(field)) is not bool:
                raise DriverError(f'invalid snapshot {field}')
        for field in ('surface', 'foregroundAppId', 'pageId'):
            if not isinstance(value.get(field), str):
                raise DriverError(f'invalid snapshot {field}')
        if value['foregroundAppId'] and not value['pageId']:
            raise DriverError('foreground App without a declared page')
        if not value['foregroundAppId'] and (value['pageId'] or value['canBack'] or value['backPending']):
            raise DriverError('page state without a foreground App')
        if value['backPending'] and value['canBack']:
            raise DriverError('pending Back cannot also accept another Back')
        self.last_seq = value['seq']
        self.snapshots.append(value)
        return value

    def wait(self, expected, *, after, timeout=None, stable_samples=2, invariants=None):
        deadline = self.clock() + (self.timeout if timeout is None else timeout)
        stable = 0
        last = None
        while self.clock() < deadline:
            last = self.snapshot()
            if invariants and any(last.get(key) != value for key, value in invariants.items()):
                raise DriverError(f'waiting invariant violated: {last}')
            matches = last['seq'] > after and not last['inputBusy'] and \
                all(last.get(key) == value for key, value in expected.items())
            stable = stable + 1 if matches else 0
            if stable >= stable_samples:
                return last
            self.sleep(0.04)
        raise DriverError(f'owner state timeout: expected {expected}, last {last}')

    def stimulate(self, name, op, expected, **parameters):
        before = self.snapshot()
        step = {'name': name, 'operation': op, 'parameters': parameters, 'beforeSeq': before['seq'],
                'expected': expected, 'status': 'RUNNING'}
        self.steps.append(step)
        try:
            self.request(op, **parameters)
            after = self.wait(expected, after=before['seq'])
        except (Exception, KeyboardInterrupt) as error:
            step.update(status='FAIL', error=f'{type(error).__name__}: {error}')
            raise
        step.update(status='PASS', afterSeq=after['seq'])
        return after

    @staticmethod
    def points(start, end=None):
        end = start if end is None else end
        if start == end:
            return [{'x': start[0], 'y': start[1], 'elapsedMs': 0, 'pressed': True},
                    {'x': end[0], 'y': end[1], 'elapsedMs': 80, 'pressed': False}]
        return [{'x': start[0], 'y': start[1], 'elapsedMs': 0, 'pressed': True},
                {'x': end[0], 'y': end[1], 'elapsedMs': 160, 'pressed': True},
                {'x': end[0], 'y': end[1], 'elapsedMs': 240, 'pressed': False}]

    def touch(self, name, expected, start, end=None):
        return self.stimulate(name, 'stimulus.touch', expected, points=self.points(start, end))

    def power(self, name, expected):
        return self.stimulate(name, 'stimulus.powerShort', expected)

    def await_state(self, name, expected, *, timeout, invariants):
        step = {'name': name, 'operation': 'observe-transition', 'beforeSeq': self.last_seq,
                'expected': expected, 'invariants': invariants, 'timeoutSeconds': timeout,
                'status': 'RUNNING'}
        self.steps.append(step)
        try:
            after = self.wait(expected, after=self.last_seq, timeout=timeout, invariants=invariants)
        except (Exception, KeyboardInterrupt) as error:
            step.update(status='FAIL', error=f'{type(error).__name__}: {error}')
            raise
        step.update(status='PASS', afterSeq=after['seq'])
        return after

    def observe(self, name, expected, duration=0.5):
        # A bounded negative assertion checks every fresh sample, not only the final one.
        deadline = self.clock() + duration
        count = 0
        step = {'name': name, 'status': 'RUNNING', 'operation': 'observe-invariant',
                'expected': expected, 'beforeSeq': self.last_seq, 'windowSeconds': duration}
        self.steps.append(step)
        try:
            while self.clock() < deadline:
                value = self.snapshot()
                count += 1
                if value['inputBusy'] or any(value.get(key) != target for key, target in expected.items()):
                    raise DriverError(f'{name}: invariant violated: {value}')
                self.sleep(0.04)
            if count < 2:
                raise DriverError(f'{name}: insufficient observations')
        except (Exception, KeyboardInterrupt) as error:
            step.update(status='FAIL', error=f'{type(error).__name__}: {error}',
                        afterSeq=self.last_seq, samples=count)
            raise
        step.update(status='PASS', afterSeq=self.last_seq, samples=count)

    def suite(self, profile):
        home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': '', 'pageId': '',
                'canBack': False, 'backPending': False}
        initial = self.snapshot()
        if initial['inputBusy']:
            raise DriverError('device already has an occupied input sequence')
        if not initial['display']:
            self.power('initial wake', {'display': True})
            initial = self.snapshot()
        if initial['foregroundAppId'] or initial['surface'] != 'watch_face':
            self.power('initial Home', home)
        else:
            self.wait(home, after=initial['seq'])
        self.touch('Watch Face to Launcher', {**home, 'surface': 'launcher'},
                   *profile['up'])
        self.touch('Launcher pull returns Home', home, *profile['launcher_pull'])
        self.touch('Watch Face to Brightness Card', {**home, 'surface': 'shell.brightness'},
                   *profile['left'])
        self.touch('Card returns Home', home, *profile['right'])
        self.touch('Watch Face to Quick Settings', {**home, 'surface': 'quick_settings'},
                   *profile['down'])
        self.touch('Quick Settings returns Home', home, *profile['up'])
        self.touch('Launcher for Native', {**home, 'surface': 'launcher'}, *profile['up'])
        root = {'foregroundAppId': 'espocket.app.hello', 'pageId': 'root', 'display': True,
                'canBack': False, 'backPending': False}
        detail = {**root, 'pageId': 'detail', 'canBack': True}
        self.touch('Open Native Root', root, profile['native_tap'])
        self.touch('Open Detail', detail, profile['detail_tap'])
        self.touch('Detail Edge Back to Root', root, *profile['edge_back'])
        self.touch('Root Edge Back remains Root', root, *profile['edge_back'])
        self.observe('Root has no Back', root)
        self.touch('Detail for Back confirmation', detail, profile['detail_tap'])
        self.touch('Enable Back confirmation', detail, profile['confirm_tap'])
        pending = {**detail, 'canBack': False, 'backPending': True}
        self.touch('Back awaits App confirmation', pending, *profile['edge_back'])
        self.touch('Repeated pending Back stays Detail', pending, *profile['edge_back'])
        self.observe('Pending Back preserves Detail', pending)
        self.touch('Cancel Back preserves Detail', detail, profile['cancel_back_tap'])
        self.touch('Back confirmation for allow', pending, *profile['edge_back'])
        self.touch('Allow Back returns Root', root, profile['allow_back_tap'])
        self.touch('Detail for Back timeout', detail, profile['detail_tap'])
        self.touch('Back confirmation for timeout', pending, *profile['edge_back'])
        self.await_state('Back timeout cancels on Detail', detail, timeout=18.0,
                         invariants={'foregroundAppId': root['foregroundAppId'],
                                     'pageId': 'detail', 'display': True})
        self.touch('Expired confirmation cannot pop', detail, profile['allow_back_tap'])
        self.observe('Expired confirmation remains Detail', detail)
        self.touch('Back confirmation before PWR Home', pending, *profile['edge_back'])
        self.power('PWR Home', home)
        self.touch('Launcher after pending PWR Home', {**home, 'surface': 'launcher'}, *profile['up'])
        self.touch('Reopen Native starts Root', root, profile['native_tap'])
        self.touch('Reopened Native Detail', detail, profile['detail_tap'])
        self.touch('Reopened Back confirmation defaults Off', root, *profile['edge_back'])
        self.power('PWR Home after reopening', home)
        self.power('PWR screen off', {**home, 'display': False})
        self.power('PWR wake', home)

    def attempt(self, profile, *, device_id, expected_image=None, attempt_id=None):
        if self.attempt_started:
            raise DriverError('create a new Driver and output directory for each attempt')
        self.attempt_started = True
        report = {'attempt': attempt_id or str(uuid.uuid4()), 'startedAt': datetime.now(timezone.utc).isoformat(),
                  'deviceId': device_id, 'deviceIdentitySource': 'operator-inventory', 'transport': 'usb-serial-jtag', 'inputType': 'synthetic-input',
                  'physicalInputVerified': False, 'visualVerified': False, 'limitations': LIMITS,
                  'profile': profile, 'status': 'RUNNING'}
        failed = None
        try:
            self.hello(expected_image)
            self.suite(profile)
        except (Exception, KeyboardInterrupt) as error:
            failed = f'{type(error).__name__}: {error}'
        # Both success and failure release before the final snapshot. Never skip cleanup on an error.
        cleanup = {}
        try:
            self.request('release')
            cleanup['release'] = 'ok'
        except (Exception, KeyboardInterrupt) as error:
            cleanup['releaseError'] = f'{type(error).__name__}: {error}'
            failed = failed or 'release failed'
        try:
            final = self.snapshot()
            cleanup['finalSnapshot'] = final
            if final['inputBusy']:
                failed = failed or 'input remains occupied after release'
        except (Exception, KeyboardInterrupt) as error:
            cleanup['snapshotError'] = f'{type(error).__name__}: {error}'
            failed = failed or 'final snapshot failed'
        try:
            deadline = self.clock() + 0.15
            while self.clock() < deadline:
                line = self.transport.readline(4096)
                if line:
                    self.raw_log.write(b'RX ' + line)
                    self.raw_log.flush()
                    self.check_log(line)
        except (Exception, KeyboardInterrupt) as error:
            cleanup['tailLogError'] = f'{type(error).__name__}: {error}'
            failed = failed or 'device error after final snapshot'
        report.update(identity=self.identity, status='FAIL' if failed else 'PASS', error=failed,
                      steps=self.steps, snapshots=self.snapshots, cleanup=cleanup,
                      finishedAt=datetime.now(timezone.utc).isoformat())
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--device-id', required=True, help='board identity from inventory, not the serial port name')
    parser.add_argument('--expected-image', required=True, help='exact hello image_identity for this build')
    parser.add_argument('--profile', type=Path, default=Path(__file__).with_name('interaction-profile-466.json'))
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/espocket-interaction'))
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text())
    directory = args.output.resolve() / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + str(uuid.uuid4()))
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / 'serial.log').open('xb') as raw_log:
        try:
            import serial  # Only the real USB CLI needs pyserial; host tests use an in-memory transport.
            with serial.Serial(args.port, 115200, timeout=0.05, write_timeout=1) as transport:
                report = Driver(transport, raw_log).attempt(profile, device_id=args.device_id,
                                                         expected_image=args.expected_image,
                                                         attempt_id=directory.name)
        except Exception as error:
            report = {'status': 'FAIL', 'attempt': directory.name, 'deviceId': args.device_id,
                      'expectedImage': args.expected_image, 'inputType': 'synthetic-input',
                      'physicalInputVerified': False, 'visualVerified': False, 'limitations': LIMITS,
                      'error': f'{type(error).__name__}: {error}', 'cleanup': 'transport unavailable'}
    report['port'] = args.port
    report['expectedImage'] = args.expected_image
    (directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['status']}: {directory / 'report.json'}")
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
