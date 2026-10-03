"""Device scenario execution, assertions and immutable attempt evidence."""
from __future__ import annotations
from datetime import datetime, timezone
import uuid
from ..e2e import navigation, cards, surfaces, apps, runtime_confirm, reclaim, resources, settings_brightness, audio_playback, store_online
from .usb_test_client import UsbTestClient, DeviceTestError

LIMITS = 'Synthetic input does not verify touch hardware, PWR GPIO, or visual feedback.'


class DeviceTestRunner(UsbTestClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.steps = []
        self.attempt_started = False

    def wait(self, expected, *, after, timeout=None, stable_samples=2, invariants=None):
        deadline = self.clock() + (self.timeout if timeout is None else timeout)
        stable = 0
        last = None
        while self.clock() < deadline:
            last = self.snapshot()
            if invariants and any(last.get(key) != value for key, value in invariants.items()):
                raise DeviceTestError(f'waiting invariant violated: {last}')
            matches = last['seq'] > after and not last['inputBusy'] and \
                all(last.get(key) == value for key, value in expected.items())
            stable = stable + 1 if matches else 0
            if stable >= stable_samples:
                return last
            self.sleep(0.04)
        raise DeviceTestError(f'owner state timeout: expected {expected}, last {last}')

    def stimulate(self, name, op, expected, *, quiet_window=0, **parameters):
        before = self.snapshot()
        step = {'name': name, 'operation': op, 'parameters': parameters, 'beforeSeq': before['seq'],
                'expected': expected, 'status': 'RUNNING'}
        if quiet_window:
            step['quietWindowSeconds'] = quiet_window
        self.steps.append(step)
        try:
            self.request(op, **parameters)
            if quiet_window:
                self.capture_logs(quiet_window)
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

    def power(self, name, expected, *, quiet_window=0):
        return self.stimulate(name, 'stimulus.powerShort', expected, quiet_window=quiet_window)

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
                    raise DeviceTestError(f'{name}: invariant violated: {value}')
                self.sleep(0.04)
            if count < 2:
                raise DeviceTestError(f'{name}: insufficient observations')
        except (Exception, KeyboardInterrupt) as error:
            step.update(status='FAIL', error=f'{type(error).__name__}: {error}',
                        afterSeq=self.last_seq, samples=count)
            raise
        step.update(status='PASS', afterSeq=self.last_seq, samples=count)

    def suite(self, profile):
        navigation.run(self, profile)

    def card_suite(self, profile):
        cards.run(self, profile)

    def attempt(self, profile, *, device_id, expected_image=None, attempt_id=None, suite="navigation"):
        if self.attempt_started:
            raise DeviceTestError('create a new DeviceTestRunner and output directory for each attempt')
        self.attempt_started = True
        report = {'attempt': attempt_id or str(uuid.uuid4()), 'startedAt': datetime.now(timezone.utc).isoformat(),
                  'deviceId': device_id, 'deviceIdentitySource': 'operator-inventory', 'transport': 'usb-serial-jtag', 'inputType': 'synthetic-input',
                  'physicalInputVerified': False, 'visualVerified': False, 'limitations': LIMITS,
                  'profile': profile, 'testSuite': suite, 'status': 'RUNNING'}
        failed = None
        try:
            self.hello(expected_image)
            if suite == 'navigation':
                self.suite(profile)
            elif suite == 'cards':
                self.card_suite(profile)
            elif suite == 'surfaces':
                surfaces.run(self, profile)
            elif suite == 'apps':
                apps.run(self, profile)
            elif suite == 'runtime-confirm':
                runtime_confirm.run(self, profile)
            elif suite == 'store-online':
                store_online.run(self, profile)
            elif suite == 'audio-playback':
                audio_playback.run(self, profile)
            elif suite == 'settings-brightness':
                settings_brightness.run(self, profile)
            elif suite == 'resources':
                resources.run(self, profile)
            elif suite in ('reclaim-native', 'reclaim-runtime'):
                reclaim.run(self, profile, suite.removeprefix('reclaim-'))
            else:
                raise DeviceTestError('unknown test suite')
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
