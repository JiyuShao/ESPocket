"""Cards device scenarios; assertions use real Owner snapshots."""

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
    for model, app, side, outward, inward in (
        ('Native', 'espocket.app.hello', 'left', 'right', 'left'),
        ('Runtime', 'espocket.app.hello_runtime', 'right', 'left', 'right'),
    ):
        card = {**home, 'surface': 'app_card.' + side}
        root = {'foregroundAppId': app, 'pageId': 'root', 'display': True,
                'canBack': False, 'backPending': False}
        detail = {**root, 'pageId': 'detail', 'canBack': True}
        runner.touch(model + ' summary Card', card, *profile[outward])
        runner.touch(model + ' summary opens Root', root, profile['card_open_tap'])
        runner.touch(model + ' Root Edge Back stays Root', root, *profile['edge_back'])
        runner.observe(model + ' Root has no Back', root)
        runner.power(model + ' Root PWR Home', home)
        runner.touch(model + ' first Card after Home', card, *profile[outward])
        runner.touch(model + ' second Card', card, *profile[outward])
        runner.touch(model + ' sequence boundary stays on last Card', card, *profile[outward])
        runner.touch(model + ' target opens Detail', detail, profile['card_open_tap'])
        runner.touch(model + ' Detail Back to Root', root, *profile['edge_back'])
        runner.power(model + ' Detail task PWR Home', home)
        runner.touch(model + ' summary after Detail task', card, *profile[outward])
        runner.touch(model + ' reopen from Root', root, profile['card_open_tap'])
        runner.power(model + ' reopened Root PWR Home', home)
        runner.touch(model + ' summary Card for pause', card, *profile[outward])
        runner.await_state(model + ' Card automatic screen off', {**card, 'display': False},
                         timeout=35, invariants={key: value for key, value in card.items() if key != 'display'})
        runner.power(model + ' Card wake restores Card', card)
        runner.touch(model + ' Card inward returns Home', home, *profile[inward])
