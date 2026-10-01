"""Verify the real Driver against controlled protocol observations, without a device."""
import importlib.util
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('interaction_driver', ROOT / 'scripts/firmware/interaction_driver.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def snapshot(seq, **fields):
    return {'seq': seq, 'surface': 'watch_face', 'display': True, 'foregroundAppId': '',
            'pageId': '', 'canBack': False, 'backPending': False, 'inputBusy': False, **fields}


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, duration):
        self.now += duration


class Transport:
    def __init__(self, responder, clock):
        self.responder = responder
        self.clock = clock
        self.requests = []
        self.pending = []

    def write(self, frame):
        request = json.loads(frame[len(MODULE.PREFIX):])
        self.requests.append(request)
        result = self.responder(request)
        if isinstance(result, list):
            self.pending.extend(result)
        else:
            reply = {'version': 1, 'request_id': request['request_id'], 'ok': True, **result}
            self.pending.append(MODULE.PREFIX + json.dumps(reply).encode() + b'\n')
        return len(frame)

    def readline(self, limit=4096):
        self.clock.now += 0.01
        return self.pending.pop(0) if self.pending else b''


class DriverTests(unittest.TestCase):
    def make(self, responder, driver_type=MODULE.Driver):
        clock = Clock()
        transport = Transport(responder, clock)
        log = io.BytesIO()
        driver = driver_type(transport, log, clock=clock, sleep=clock.sleep,
                             timeout=0.3, request_seed=100)
        return driver, transport, log

    def test_ack_and_busy_do_not_satisfy_owner_assertion(self):
        states = iter([snapshot(1), snapshot(2, surface='launcher', inputBusy=True),
                       snapshot(3), snapshot(4, surface='launcher'), snapshot(5, surface='launcher')])
        driver, transport, _ = self.make(lambda request:
            {'snapshot': next(states)} if request['op'] == 'snapshot' else {})
        result = driver.touch('Launcher', {'surface': 'launcher'}, [233, 350], [233, 130])
        self.assertEqual(result['seq'], 5)
        self.assertEqual(driver.steps[0]['afterSeq'], 5)
        self.assertEqual([r['op'] for r in transport.requests].count('snapshot'), 5)

    def test_protocol_error_is_not_automatically_retried(self):
        driver, transport, _ = self.make(lambda _: {'ok': False, 'error_code': 'invalid_state'})
        with self.assertRaisesRegex(MODULE.DriverError, 'invalid_state'):
            driver.request('snapshot')
        self.assertEqual(len(transport.requests), 1)

    def test_nonadvancing_sequence_and_invalid_boolean_fail(self):
        driver, _, _ = self.make(lambda _: {'snapshot': snapshot(1)})
        driver.snapshot()
        with self.assertRaisesRegex(MODULE.DriverError, 'did not advance'):
            driver.snapshot()
        driver, _, _ = self.make(lambda _: {'snapshot': snapshot(1, display=1)})
        with self.assertRaisesRegex(MODULE.DriverError, 'display'):
            driver.snapshot()

    def test_wait_times_out_when_owner_never_changes_despite_ack(self):
        sequence = 0
        def respond(request):
            nonlocal sequence
            sequence += 1
            return {'snapshot': snapshot(sequence)} if request['op'] == 'snapshot' else {}
        driver, _, _ = self.make(respond)
        with self.assertRaisesRegex(MODULE.DriverError, 'owner state timeout'):
            driver.touch('Launcher', {'surface': 'launcher'}, [233, 350], [233, 130])
        self.assertEqual(driver.steps[0]['status'], 'FAIL')

    def test_failed_attempt_releases_then_samples_and_keeps_new_attempt_identity(self):
        class Failed(MODULE.Driver):
            def suite(self, profile):
                self.request('stimulus.powerShort')
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image-1', 'capabilities': sorted(MODULE.CAPABILITIES)}
            if request['op'] == 'stimulus.powerShort':
                return {'ok': False, 'error_code': 'busy'}
            return {'snapshot': snapshot(1)} if request['op'] == 'snapshot' else {}
        driver, transport, log = self.make(respond, Failed)
        first = driver.attempt({}, device_id='board-1', expected_image='image-1')
        self.assertEqual(first['status'], 'FAIL')
        self.assertEqual([r['op'] for r in transport.requests],
                         ['hello', 'stimulus.powerShort', 'release', 'snapshot'])
        self.assertEqual(first['cleanup']['release'], 'ok')
        self.assertFalse(first['physicalInputVerified'])
        self.assertFalse(first['visualVerified'])
        self.assertIn(b'busy', log.getvalue())
        second, _, _ = self.make(respond, Failed)
        self.assertNotEqual(first['attempt'], second.attempt({}, device_id='board-1')['attempt'])

    def test_cleanup_failure_still_collects_final_snapshot(self):
        class Empty(MODULE.Driver):
            def suite(self, profile):
                pass
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image', 'capabilities': sorted(MODULE.CAPABILITIES)}
            if request['op'] == 'release':
                return {'ok': False, 'error_code': 'internal'}
            return {'snapshot': snapshot(1, inputBusy=True)}
        driver, transport, _ = self.make(respond, Empty)
        report = driver.attempt({}, device_id='board-1')
        self.assertEqual(report['status'], 'FAIL')
        self.assertIn('releaseError', report['cleanup'])
        self.assertTrue(report['cleanup']['finalSnapshot']['inputBusy'])
        self.assertEqual(transport.requests[-1]['op'], 'snapshot')

    def test_image_mismatch_is_failure_before_stimulus(self):
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'wrong', 'capabilities': sorted(MODULE.CAPABILITIES)}
            return {'snapshot': snapshot(1)} if request['op'] == 'snapshot' else {}
        driver, transport, _ = self.make(respond)
        report = driver.attempt({}, device_id='board-1', expected_image='required')
        self.assertEqual(report['status'], 'FAIL')
        self.assertFalse(any(r['op'].startswith('stimulus.') for r in transport.requests))
        self.assertEqual(transport.requests[-2]['op'], 'release')

    def test_no_back_observation_rejects_transient_violation(self):
        states = iter([snapshot(1), snapshot(2, foregroundAppId='app', pageId='detail', canBack=True)])
        driver, _, _ = self.make(lambda _: {'snapshot': next(states)})
        with self.assertRaisesRegex(MODULE.DriverError, 'invariant violated'):
            driver.observe('Root no Back', {'canBack': False})

    def test_stale_response_and_chatter_cannot_satisfy_current_request(self):
        def respond(request):
            def frame(identifier):
                return MODULE.PREFIX + json.dumps({'version': 1, 'request_id': identifier, 'ok': True}).encode() + b'\n'
            return [b'ordinary device log\n', frame(request['request_id'] - 1), frame(request['request_id'])]
        driver, _, log = self.make(respond)
        self.assertTrue(driver.request('release')['ok'])
        self.assertIn(b'ordinary device log', log.getvalue())

    def test_device_error_log_fails_current_operation(self):
        driver, _, log = self.make(lambda _: [b'Synthetic input tick failed: timeout\n'])
        with self.assertRaisesRegex(MODULE.DriverError, 'device error observed'):
            driver.request('snapshot')
        self.assertIn(b'timeout', log.getvalue())

    def test_tail_device_error_is_retained_and_cannot_be_reported_as_pass(self):
        class Empty(MODULE.Driver):
            def suite(self, profile):
                pass
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image', 'capabilities': sorted(MODULE.CAPABILITIES)}
            if request['op'] == 'snapshot':
                reply = {'version': 1, 'request_id': request['request_id'], 'ok': True,
                         'snapshot': snapshot(1)}
                return [MODULE.PREFIX + json.dumps(reply).encode() + b'\n',
                        b'Guru Meditation Error: core panic\n']
            return {}
        driver, _, log = self.make(respond, Empty)
        result = driver.attempt({}, device_id='board-1')
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('tailLogError', result['cleanup'])
        self.assertIn(b'Guru Meditation', log.getvalue())
        with self.assertRaisesRegex(MODULE.DriverError, 'new Driver'):
            driver.attempt({}, device_id='board-1')

    def test_partial_write_cannot_be_acknowledged_as_success(self):
        driver, transport, _ = self.make(lambda _: {})
        transport.write = lambda frame: len(frame) - 1
        with self.assertRaisesRegex(MODULE.DriverError, 'partial request write'):
            driver.request('release')

    def test_suite_contains_required_semantic_paths(self):
        class Recording(MODULE.Driver):
            def snapshot(self):
                self.last_seq += 1
                return snapshot(self.last_seq)
            def wait(self, expected, **options):
                return snapshot(self.last_seq + 1, **expected)
            def touch(self, name, expected, *coordinates):
                self.steps.append({'name': name, 'expected': expected})
            def power(self, name, expected):
                self.steps.append({'name': name, 'expected': expected})
            def observe(self, name, expected, **options):
                self.steps.append({'name': name, 'expected': expected})
        driver, _, _ = self.make(lambda _: {}, Recording)
        profile = json.loads((ROOT / 'scripts/firmware/interaction-profile-466.json').read_text())
        driver.suite(profile)
        by_name = {step['name']: step['expected'] for step in driver.steps}
        self.assertEqual(by_name['Watch Face to Launcher']['surface'], 'launcher')
        self.assertEqual(by_name['Watch Face to Brightness Card']['surface'], 'shell.brightness')
        self.assertEqual(by_name['Detail Edge Back to Root']['pageId'], 'root')
        self.assertFalse(by_name['Root has no Back']['canBack'])
        self.assertEqual(by_name['PWR Home']['surface'], 'watch_face')
        self.assertFalse(by_name['PWR screen off']['display'])
        self.assertTrue(by_name['PWR wake']['display'])


if __name__ == '__main__':
    unittest.main()
