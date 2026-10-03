"""Explicit Audio fixture: real playback, Home cleanup, then successful replay."""
from ..support.usb_test_client import DeviceTestError


def run(runner, profile):
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': ''}
    root = {'foregroundAppId': 'brookesia.general.settings', 'pageId': 'settings.root', 'display': True}
    sound = {**root, 'pageId': 'settings.sound'}
    state = runner.snapshot()
    if not state['display']:
        runner.power('wake', {'display': True})
    if state['foregroundAppId'] or state['surface'] != 'watch_face':
        runner.power('initial Home', home)
    original = runner.check_log
    counts = {'playing': 0, 'cleanup': 0}

    def check(line):
        original(line)
        if b'Owner state: Playing' in line:
            counts['playing'] += 1
        if b'Stopped and removed owned fixture' in line:
            counts['cleanup'] += 1
        if any(token in line for token in (b'the channel has not been enabled yet',
                                          b'AUDIO-PROBE Start failed', b'Failed to deinit codec')):
            raise DeviceTestError('Audio Owner or I2S teardown failed')

    runner.check_log = check
    try:
        for cycle in range(2):
            before = counts.copy()
            runner.touch(f'Quick Settings {cycle}', {'surface': 'quick_settings'}, *profile['down'])
            runner.touch(f'Settings {cycle}', root, profile['quick_settings_app_tap'])
            runner.touch(f'Play {cycle}', sound, profile['settings_sound_tap'])
            runner.capture_logs(3)
            if counts['playing'] <= before['playing']:
                raise DeviceTestError('fixture did not reach actual Owner Playing')
            runner.power(f'Home stops playback {cycle}', home)
            runner.capture_logs(2)
            if counts['cleanup'] != before['cleanup'] + 1:
                raise DeviceTestError('Home did not clean its owned playback fixture')
    finally:
        runner.check_log = original
