"""Explicit Runtime privacy fixture gate; not an ordinary firmware suite."""
import time


def run(runner, log, profile):
    home = {'surface': 'watch_face', 'foregroundAppId': '', 'display': True}
    state = runner.snapshot()
    if not state['display']:
        runner.power('Wake', {'display': True})
    if state['foregroundAppId'] or state['surface'] != 'watch_face':
        runner.power('Home', home)
    runner.touch('Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
    owner = {'foregroundAppId': 'espocket.app.hello_runtime', 'pageId': 'root', 'display': True}
    runner.touch('Isolation owner', owner, profile['runtime_tap'])

    def fresh(offset):
        return log.read_bytes()[offset:]

    def wait_marker(marker, offset, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            runner.capture_logs(.1)
            data = fresh(offset)
            if b'KISO FIXTURE_ERROR' in data or b'KISO FAIL_CROSS_OWNER_RESULT' in data:
                raise RuntimeError('Fixture failure or cross-owner keyboard delivery; see serial log')
            if marker in data:
                return data
        raise RuntimeError('Missing positive fixture marker: ' + marker.decode())

    for index in range(2):
        offset = log.stat().st_size
        runner.touch('Start observer and owner keyboard', owner, profile['runtime_detail_tap'])
        before = wait_marker(f'KISO KEYBOARD_OPEN {index}'.encode(), offset)
        # Timer canary positively proves the corresponding real observer is active.
        runner.capture_logs(.5)
        assert f'KISO OBSERVER_TICK {index} '.encode() in fresh(offset), 'observer positive canary absent'
        # Round keyboard's lower-right Ready key; seeded text is synthetic only.
        runner.touch('Confirm synthetic owner input', owner, [363, 370])
        completed = wait_marker(f'KISO STOP_COMPLETE {index}'.encode(), offset)
        assert f'KISO OWNER_RESULT {index}'.encode() in completed, 'owner did not receive its input'
        assert f'KISO OBSERVER_PUBLIC_EVENT {index}'.encode() in log.read_bytes(), 'public event positive control absent'
        cutoff = log.stat().st_size
        runner.capture_logs(1.2)
        after = fresh(cutoff)
        assert f'KISO OBSERVER_TICK {index} '.encode() not in after, 'stopped instance timer survived'
        assert f'KISO OBSERVER_PUBLIC_EVENT {index}'.encode() not in after, 'stopped instance subscription survived'
    # Core's expected failed-stop alert auto-closes after 3000 ms.
    # Wait for it before sending the next App click, without bypassing the alert.
    runner.capture_logs(3.2)
    cutoff = log.stat().st_size
    runner.touch('Public event after both observers stopped', owner, profile['runtime_detail_tap'])
    wait_marker(b'KISO POST_STOP_PUBLIC_DONE', cutoff)
    assert b'KISO OWNER_PUBLIC_EVENT' in fresh(cutoff), 'post-stop public event did not occur'
    runner.power('Owner Home after temporary observer coordination', home)
    runner.touch('Native Launcher after failed Runtime stop', {**home, 'surface': 'launcher'}, *profile['up'])
    runner.touch('Native remains usable', {'foregroundAppId': 'espocket.app.hello', 'pageId': 'root'}, profile['native_tap'])
    runner.power('Final Home', home)
    runner.capture_logs(.5)
    assert b'KISO OBSERVER_PUBLIC_EVENT' not in fresh(cutoff), 'revoked observer received later public events'
    assert b'KISO_PRIVATE_PROBE' not in log.read_bytes(), 'keyboard plaintext was logged'

