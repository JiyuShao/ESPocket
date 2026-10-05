"""Native/Runtime navigation and unreclaimed wake on ordinary firmware."""
from ..support.usb_test_client import DeviceTestError


def run(runner, profile):
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': '',
            'pageId': '', 'canBack': False, 'backPending': False}
    initial = runner.snapshot()
    if initial['inputBusy']:
        raise DeviceTestError('device already has an occupied input sequence')
    if not initial['display']:
        runner.power('initial wake', {'display': True})
        initial = runner.snapshot()
    if initial['foregroundAppId'] or initial['surface'] != 'watch_face':
        runner.power('initial Home', home)
    for model, manifest, launch, open_detail in (
        ('Native', 'espocket.app.hello', 'native_tap', 'detail_tap'),
        ('Runtime', 'espocket.app.hello_runtime', 'runtime_tap', 'runtime_detail_tap'),
    ):
        root = {'foregroundAppId': manifest, 'pageId': 'root', 'display': True,
                'canBack': False, 'backPending': False}
        detail = {**root, 'pageId': 'detail', 'canBack': True}
        pending = {**detail, 'canBack': False, 'backPending': True}
        runner.touch(model + ' Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
        runner.stimulate(model + ' Root', 'stimulus.touch', root,
                         quiet_window=8 if model == 'Runtime' else 0,
                         points=runner.points(profile[launch]))
        runner.touch(model + ' Root cannot Back', root, *profile['edge_back'])
        runner.observe(model + ' Root stays Root', root)
        runner.touch(model + ' Detail', detail, profile[open_detail])
        runner.touch(model + ' ordinary horizontal', detail, *profile['app_horizontal'])
        runner.observe(model + ' horizontal stays Detail', detail)
        runner.touch(model + ' Back to Root', root, *profile['edge_back'])
        runner.touch(model + ' Detail for wake', detail, profile[open_detail])
        runner.await_state(model + ' automatic screen off', {**detail, 'display': False},
                           timeout=35, invariants={'foregroundAppId': manifest, 'pageId': 'detail'})
        runner.power(model + ' wake preserves Detail', detail)
        runner.touch(model + ' confirmation On', detail, profile['confirm_tap'])
        runner.touch(model + ' deferred Back', pending, *profile['edge_back'])
        runner.touch(model + ' repeated Back remains pending', pending, *profile['edge_back'])
        runner.touch(model + ' cancel Back', detail, profile['cancel_back_tap'])
        runner.touch(model + ' deferred Back for allow', pending, *profile['edge_back'])
        runner.touch(model + ' allow Back', root, profile['allow_back_tap'])
        runner.touch(model + ' Detail for timeout', detail, profile[open_detail])
        runner.touch(model + ' deferred Back for timeout', pending, *profile['edge_back'])
        runner.await_state(model + ' timeout cancels Back', detail, timeout=18,
                           invariants={'foregroundAppId': manifest, 'pageId': 'detail', 'display': True})
        runner.touch(model + ' expired allow cannot Back', detail, profile['allow_back_tap'])
        runner.touch(model + ' deferred Back before Home', pending, *profile['edge_back'])
        runner.power(model + ' pending Home', home)
        runner.touch(model + ' Launcher after Home', {**home, 'surface': 'launcher'}, *profile['up'])
        runner.stimulate(model + ' relaunch starts Root', 'stimulus.touch', root,
                         quiet_window=8 if model == 'Runtime' else 0,
                         points=runner.points(profile[launch]))
        runner.touch(model + ' new Detail', detail, profile[open_detail])
        runner.touch(model + ' new instance defaults to immediate Back', root, *profile['edge_back'])
        runner.power(model + ' final Home', home)
