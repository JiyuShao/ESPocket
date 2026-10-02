"""Navigation device scenarios; assertions use real Owner snapshots."""

from ..support.usb_test_client import DeviceTestError

def run(runner, profile):
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': '', 'pageId': '',
            'canBack': False, 'backPending': False}
    initial = runner.snapshot()
    if initial['inputBusy']:
        raise DeviceTestError('device already has an occupied input sequence')
    if not initial['display']:
        runner.power('initial wake', {'display': True})
        initial = runner.snapshot()
    if initial['foregroundAppId'] or initial['surface'] != 'watch_face':
        runner.power('initial Home', home)
    else:
        runner.wait(home, after=initial['seq'])
    runner.touch('Watch Face to Launcher', {**home, 'surface': 'launcher'},
               *profile['up'])
    runner.touch('Launcher pull returns Home', home, *profile['launcher_pull'])
    runner.touch('Watch Face to Brightness Card', {**home, 'surface': 'shell.brightness'},
               *profile['left'])
    runner.touch('Card returns Home', home, *profile['right'])
    runner.touch('Watch Face to Quick Settings', {**home, 'surface': 'quick_settings'},
               *profile['down'])
    runner.touch('Quick Settings returns Home', home, *profile['up'])
    runner.touch('Launcher for Native', {**home, 'surface': 'launcher'}, *profile['up'])
    root = {'foregroundAppId': 'espocket.app.hello', 'pageId': 'root', 'display': True,
            'canBack': False, 'backPending': False}
    detail = {**root, 'pageId': 'detail', 'canBack': True}
    runner.touch('Open Native Root', root, profile['native_tap'])
    runner.touch('Open Detail', detail, profile['detail_tap'])
    runner.touch('Detail Edge Back to Root', root, *profile['edge_back'])
    runner.touch('Root Edge Back remains Root', root, *profile['edge_back'])
    runner.observe('Root has no Back', root)
    runner.touch('Detail for Back confirmation', detail, profile['detail_tap'])
    runner.touch('Enable Back confirmation', detail, profile['confirm_tap'])
    pending = {**detail, 'canBack': False, 'backPending': True}
    runner.touch('Back awaits App confirmation', pending, *profile['edge_back'])
    runner.touch('Repeated pending Back stays Detail', pending, *profile['edge_back'])
    runner.observe('Pending Back preserves Detail', pending)
    runner.touch('Cancel Back preserves Detail', detail, profile['cancel_back_tap'])
    runner.touch('Back confirmation for allow', pending, *profile['edge_back'])
    runner.touch('Allow Back returns Root', root, profile['allow_back_tap'])
    runner.touch('Detail for Back timeout', detail, profile['detail_tap'])
    runner.touch('Back confirmation for timeout', pending, *profile['edge_back'])
    runner.await_state('Back timeout cancels on Detail', detail, timeout=18.0,
                     invariants={'foregroundAppId': root['foregroundAppId'],
                                 'pageId': 'detail', 'display': True})
    runner.touch('Expired confirmation cannot pop', detail, profile['allow_back_tap'])
    runner.observe('Expired confirmation remains Detail', detail)
    runner.touch('Back confirmation before PWR Home', pending, *profile['edge_back'])
    runner.power('PWR Home', home)
    runner.touch('Launcher after pending PWR Home', {**home, 'surface': 'launcher'}, *profile['up'])
    runner.touch('Reopen Native starts Root', root, profile['native_tap'])
    runner.touch('Reopened Native Detail', detail, profile['detail_tap'])
    runner.touch('Reopened Back confirmation defaults Off', root, *profile['edge_back'])
    runner.power('PWR Home after reopening', home)
    runner.power('PWR screen off', {**home, 'display': False})
    runner.power('PWR wake', home)
