"""Minimal regression for Runtime async confirmation and its GUI feedback."""
from ..support.usb_test_client import DeviceTestError


def run(runner, profile):
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': '',
            'pageId': '', 'canBack': False, 'backPending': False}
    state = runner.snapshot()
    if state['inputBusy']:
        raise DeviceTestError('device already has an occupied input sequence')
    if not state['display']:
        runner.power('initial wake', {'display': True})
        state = runner.snapshot()
    if state['foregroundAppId'] or state['surface'] != 'watch_face':
        runner.power('initial Home', home)
    root = {'foregroundAppId': 'espocket.app.hello_runtime', 'pageId': 'root',
            'display': True, 'canBack': False, 'backPending': False}
    detail = {**root, 'pageId': 'detail', 'canBack': True}
    runner.touch('Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
    runner.touch('Runtime Root', root, profile['runtime_tap'])
    runner.touch('Runtime Detail', detail, profile['runtime_detail_tap'])
    runner.touch('Confirmation On', detail, profile['confirm_tap'])
    runner.touch('Deferred Back', {**detail, 'canBack': False, 'backPending': True},
                 *profile['edge_back'])
    runner.observe('Confirmation feedback remains live',
                   {**detail, 'canBack': False, 'backPending': True})
    runner.power('PWR Home while pending', home)
