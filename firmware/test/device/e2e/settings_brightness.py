"""Repeated real Settings slider input; no theme changes, stop on the first failure."""
from ..support.usb_test_client import DeviceTestError


def run(runner, profile):
    config = profile['settings_brightness']
    cycles = config['cycles']
    if not isinstance(cycles, int) or not 1 <= cycles <= 1000:
        raise DeviceTestError('invalid brightness cycle count')
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': ''}
    root = {'foregroundAppId': 'brookesia.general.settings', 'pageId': 'settings.root', 'display': True}
    display = {**root, 'pageId': 'settings.display'}
    state = runner.snapshot()
    if state['inputBusy']:
        raise DeviceTestError('input sequence already active')
    if not state['display']:
        runner.power('initial wake', {'display': True})
    if state['foregroundAppId'] or state['surface'] != 'watch_face':
        runner.power('initial Home', home)
    runner.touch('Quick Settings', {'surface': 'quick_settings'}, *profile['down'])
    runner.touch('Settings', root, profile['quick_settings_app_tap'])
    runner.touch('Display', display, config['rootTap'])

    def drag(name, start, end, interval):
        points = [{'x': round(start[0] + (end[0] - start[0]) * i / 4),
                   'y': round(start[1] + (end[1] - start[1]) * i / 4),
                   'elapsedMs': i * interval, 'pressed': True} for i in range(5)]
        points.append({'x': end[0], 'y': end[1], 'elapsedMs': 5 * interval, 'pressed': False})
        runner.stimulate(name, 'stimulus.touch', display, points=points)

    for i in range(2):
        drag(f'scroll to slider {i + 1}', *config['scroll'], 100)
    owner_calls = 0
    original_checker = runner.check_log

    def check_slider_log(line):
        nonlocal owner_calls
        original_checker(line)
        if b'(set_brightness_internal)' in line and b'Set brightness:' in line:
            owner_calls += 1
        if b'[Display:SetBacklightBrightness]' in line and b'wait timeout' in line:
            raise DeviceTestError('actual Display brightness service timed out')

    runner.check_log = check_slider_log
    try:
        for i in range(cycles):
            before = owner_calls
            start, end = config['slider'] if i % 2 == 0 else reversed(config['slider'])
            drag(f'brightness alternating drag {i + 1}', start, end, 40)
            runner.capture_logs(0.1)
            runner.steps[-1]['brightnessOwnerCalls'] = owner_calls - before
            if owner_calls == before:
                raise DeviceTestError('inconclusive: slider input did not reach the brightness Owner')
        runner.touch('actual Back after slider stress', root, *profile['edge_back'])
        runner.power('Home after slider stress', home)
    finally:
        runner.check_log = original_checker
