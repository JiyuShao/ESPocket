"""One selected-model reclaim path and one unaffected-model wake path."""
from ..support.usb_test_client import DeviceTestError


def run(runner, profile, selected):
    if selected not in ('native', 'runtime'):
        raise DeviceTestError('unknown reclaim model')
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
    for model, manifest, launch, detail_tap in (
        ('native', 'espocket.app.hello', 'native_tap', 'detail_tap'),
        ('runtime', 'espocket.app.hello_runtime', 'runtime_tap', 'runtime_detail_tap'),
    ):
        root = {'foregroundAppId': manifest, 'pageId': 'root', 'display': True,
                'canBack': False, 'backPending': False}
        detail = {**root, 'pageId': 'detail', 'canBack': True}
        runner.touch(model + ' Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
        runner.touch(model + ' Root', root, profile[launch])
        runner.touch(model + ' Detail', detail, profile[detail_tap])
        if model == selected:
            runner.touch(model + ' confirmation On', detail, profile['confirm_tap'])
            runner.await_state(model + ' reclaimed while off', {**home, 'display': False},
                               timeout=35, invariants={})
            runner.power(model + ' wake falls back Home', home)
            runner.touch(model + ' relaunch Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
            runner.touch(model + ' relaunch starts Root', root, profile[launch])
            runner.touch(model + ' new Detail', detail, profile[detail_tap])
            runner.touch(model + ' old confirmation state cleared', root, *profile['edge_back'])
        else:
            runner.await_state(model + ' unaffected screen off', {**detail, 'display': False},
                               timeout=35, invariants={'foregroundAppId': manifest, 'pageId': 'detail'})
            runner.power(model + ' unaffected wake preserves Detail', detail)
        runner.power(model + ' final Home', home)
