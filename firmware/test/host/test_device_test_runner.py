"""Verify the real device runner against controlled protocol observations, without a device."""
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT))
from firmware.test.device.support import device_test_runner as MODULE
from firmware.test.device.support.usb_test_client import PREFIX, CAPABILITIES, DeviceTestError


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
        request = json.loads(frame[len(PREFIX):])
        self.requests.append(request)
        result = self.responder(request)
        if isinstance(result, list):
            self.pending.extend(result)
        else:
            reply = {'version': 1, 'request_id': request['request_id'], 'ok': True, **result}
            self.pending.append(PREFIX + json.dumps(reply).encode() + b'\n')
        return len(frame)

    def readline(self, limit=4096):
        self.clock.now += 0.01
        return self.pending.pop(0) if self.pending else b''


class DeviceTestRunnerTests(unittest.TestCase):
    def make(self, responder, driver_type=MODULE.DeviceTestRunner):
        clock = Clock()
        transport = Transport(responder, clock)
        log = io.BytesIO()
        driver = driver_type(transport, log, clock=clock, sleep=clock.sleep,
                             timeout=0.3, request_seed=100)
        return driver, transport, log

    def test_scenarios_reject_initial_busy_input_without_stimulus(self):
        for scenario in (MODULE.navigation, MODULE.cards, MODULE.surfaces, MODULE.apps, MODULE.runtime_confirm):
            with self.subTest(scenario=scenario.__name__):
                driver, transport, _ = self.make(lambda _: {'snapshot': snapshot(1, inputBusy=True)})
                with self.assertRaisesRegex(DeviceTestError, 'occupied input'):
                    scenario.run(driver, {})
                self.assertEqual([request['op'] for request in transport.requests], ['snapshot'])

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
        with self.assertRaisesRegex(DeviceTestError, 'invalid_state'):
            driver.request('snapshot')
        self.assertEqual(len(transport.requests), 1)

    def test_nonadvancing_sequence_and_invalid_boolean_fail(self):
        driver, _, _ = self.make(lambda _: {'snapshot': snapshot(1)})
        driver.snapshot()
        with self.assertRaisesRegex(DeviceTestError, 'did not advance'):
            driver.snapshot()
        driver, _, _ = self.make(lambda _: {'snapshot': snapshot(1, display=1)})
        with self.assertRaisesRegex(DeviceTestError, 'display'):
            driver.snapshot()

    def test_wait_times_out_when_owner_never_changes_despite_ack(self):
        sequence = 0
        def respond(request):
            nonlocal sequence
            sequence += 1
            return {'snapshot': snapshot(sequence)} if request['op'] == 'snapshot' else {}
        driver, _, _ = self.make(respond)
        with self.assertRaisesRegex(DeviceTestError, 'owner state timeout'):
            driver.touch('Launcher', {'surface': 'launcher'}, [233, 350], [233, 130])
        self.assertEqual(driver.steps[0]['status'], 'FAIL')

    def test_failed_attempt_releases_then_samples_and_keeps_new_attempt_identity(self):
        class Failed(MODULE.DeviceTestRunner):
            def suite(self, profile):
                self.request('stimulus.powerShort')
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image-1', 'capabilities': sorted(CAPABILITIES)}
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
        class Empty(MODULE.DeviceTestRunner):
            def suite(self, profile):
                pass
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image', 'capabilities': sorted(CAPABILITIES)}
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
                return {'image_identity': 'wrong', 'capabilities': sorted(CAPABILITIES)}
            return {'snapshot': snapshot(1)} if request['op'] == 'snapshot' else {}
        driver, transport, _ = self.make(respond)
        report = driver.attempt({}, device_id='board-1', expected_image='required')
        self.assertEqual(report['status'], 'FAIL')
        self.assertFalse(any(r['op'].startswith('stimulus.') for r in transport.requests))
        self.assertEqual(transport.requests[-2]['op'], 'release')

    def test_no_back_observation_rejects_transient_violation(self):
        states = iter([snapshot(1), snapshot(2, foregroundAppId='app', pageId='detail', canBack=True)])
        driver, _, _ = self.make(lambda _: {'snapshot': next(states)})
        with self.assertRaisesRegex(DeviceTestError, 'invariant violated'):
            driver.observe('Root no Back', {'canBack': False})
        self.assertEqual(driver.steps[0]['status'], 'FAIL')
        self.assertEqual(driver.steps[0]['afterSeq'], 2)
        self.assertEqual(driver.steps[0]['samples'], 2)

    def test_pending_back_cannot_accept_another_back(self):
        driver, _, _ = self.make(lambda _: {'snapshot': snapshot(
            1, foregroundAppId='app', pageId='detail', canBack=True, backPending=True)})
        with self.assertRaisesRegex(DeviceTestError, 'pending Back'):
            driver.snapshot()

    def test_timeout_transition_waits_for_fresh_owner_samples(self):
        pending = {'foregroundAppId': 'app', 'pageId': 'detail', 'backPending': True}
        states = iter([snapshot(1, **pending), snapshot(2, **pending),
                       snapshot(3, foregroundAppId='app', pageId='detail', canBack=True),
                       snapshot(4, foregroundAppId='app', pageId='detail', canBack=True)])
        driver, _, _ = self.make(lambda _: {'snapshot': next(states)})
        driver.snapshot()
        result = driver.await_state('timeout', {'canBack': True, 'backPending': False}, timeout=0.3,
                                    invariants={'foregroundAppId': 'app', 'pageId': 'detail', 'display': True})
        self.assertEqual(result['seq'], 4)
        self.assertEqual(driver.steps[0]['status'], 'PASS')
        self.assertEqual(driver.steps[0]['beforeSeq'], 1)
        self.assertEqual(driver.steps[0]['afterSeq'], 4)

    def test_timeout_transition_cannot_hide_a_wrong_page(self):
        states = iter([snapshot(1, foregroundAppId='app', pageId='detail', backPending=True),
                       snapshot(2, foregroundAppId='app', pageId='root')])
        driver, _, _ = self.make(lambda _: {'snapshot': next(states)})
        driver.snapshot()
        with self.assertRaisesRegex(DeviceTestError, 'invariant violated'):
            driver.await_state('timeout', {'canBack': True}, timeout=0.3,
                               invariants={'foregroundAppId': 'app', 'pageId': 'detail'})
        self.assertEqual(driver.steps[0]['status'], 'FAIL')

    def test_uncompleted_transition_keeps_failure_evidence(self):
        sequence = 0
        def respond(_):
            nonlocal sequence
            sequence += 1
            return {'snapshot': snapshot(sequence, foregroundAppId='app', pageId='detail', backPending=True)}
        driver, _, _ = self.make(respond)
        driver.snapshot()
        with self.assertRaisesRegex(DeviceTestError, 'owner state timeout'):
            driver.await_state('timeout', {'backPending': False}, timeout=0.1,
                               invariants={'foregroundAppId': 'app', 'pageId': 'detail'})
        self.assertEqual(driver.steps[0]['status'], 'FAIL')
        self.assertIn('owner state timeout', driver.steps[0]['error'])

    def test_stale_response_and_chatter_cannot_satisfy_current_request(self):
        def respond(request):
            def frame(identifier):
                return PREFIX + json.dumps({'version': 1, 'request_id': identifier, 'ok': True}).encode() + b'\n'
            return [b'ordinary device log\n', frame(request['request_id'] - 1), frame(request['request_id'])]
        driver, _, log = self.make(respond)
        self.assertTrue(driver.request('release')['ok'])
        self.assertIn(b'ordinary device log', log.getvalue())

    def test_stack_overflow_log_fails_before_reboot(self):
        with self.assertRaisesRegex(DeviceTestError, 'device error observed'):
            MODULE.DeviceTestRunner.check_log(b'***ERROR*** A stack overflow in task espocket_test_u has been detected.\n')

    def test_device_error_log_fails_current_operation(self):
        driver, _, log = self.make(lambda _: [b'Synthetic input tick failed: timeout\n'])
        with self.assertRaisesRegex(DeviceTestError, 'device error observed'):
            driver.request('snapshot')
        self.assertIn(b'timeout', log.getvalue())

    def test_tail_device_error_is_retained_and_cannot_be_reported_as_pass(self):
        class Empty(MODULE.DeviceTestRunner):
            def suite(self, profile):
                pass
        def respond(request):
            if request['op'] == 'hello':
                return {'image_identity': 'image', 'capabilities': sorted(CAPABILITIES)}
            if request['op'] == 'snapshot':
                reply = {'version': 1, 'request_id': request['request_id'], 'ok': True,
                         'snapshot': snapshot(1)}
                return [PREFIX + json.dumps(reply).encode() + b'\n',
                        b'Guru Meditation Error: core panic\n']
            return {}
        driver, _, log = self.make(respond, Empty)
        result = driver.attempt({}, device_id='board-1')
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('tailLogError', result['cleanup'])
        self.assertIn(b'Guru Meditation', log.getvalue())
        with self.assertRaisesRegex(DeviceTestError, 'new DeviceTestRunner'):
            driver.attempt({}, device_id='board-1')

    def test_partial_write_cannot_be_acknowledged_as_success(self):
        driver, transport, _ = self.make(lambda _: {})
        transport.write = lambda frame: len(frame) - 1
        with self.assertRaisesRegex(DeviceTestError, 'partial request write'):
            driver.request('release')

    def test_suite_contains_required_semantic_paths(self):
        class Recording(MODULE.DeviceTestRunner):
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
        profile = json.loads((ROOT / 'firmware/test/device/profiles/circular-466.json').read_text())
        driver.suite(profile)
        by_name = {step['name']: step['expected'] for step in driver.steps}
        self.assertEqual(by_name['Watch Face to Launcher']['surface'], 'launcher')
        self.assertEqual(by_name['Watch Face to Brightness Card']['surface'], 'shell.brightness')
        self.assertEqual(by_name['Detail Edge Back to Root']['pageId'], 'root')
        self.assertFalse(by_name['Root has no Back']['canBack'])
        self.assertEqual(by_name['PWR Home']['surface'], 'watch_face')
        self.assertFalse(by_name['PWR screen off']['display'])
        self.assertTrue(by_name['PWR wake']['display'])
        self.assertTrue(by_name['Back awaits App confirmation']['backPending'])
        self.assertFalse(by_name['Repeated pending Back stays Detail']['canBack'])
        self.assertEqual(by_name['Cancel Back preserves Detail']['pageId'], 'detail')
        self.assertEqual(by_name['Allow Back returns Root']['pageId'], 'root')
        self.assertFalse(by_name['Back timeout cancels on Detail']['backPending'])
        self.assertEqual(by_name['Expired confirmation cannot pop']['pageId'], 'detail')
        self.assertEqual(by_name['Reopen Native starts Root']['pageId'], 'root')
        self.assertEqual(by_name['Reopened Back confirmation defaults Off']['pageId'], 'root')


if __name__ == '__main__':
    unittest.main()
