"""Three bounded App cycles with repeatable Watch Face heap/stack checkpoints."""
from . import runtime_confirm
from ..support.usb_test_client import DeviceTestError


def run(runner, profile):
    home = {'surface': 'watch_face', 'display': True, 'foregroundAppId': '',
            'pageId': '', 'canBack': False, 'backPending': False}
    if runner.snapshot()['inputBusy']:
        raise DeviceTestError('device already has an occupied input sequence')
    for cycle in range(1, 4):
        runtime_confirm.run(runner, profile)
        runner.power(f'Runtime resource checkpoint {cycle}', {**home, 'display': False})
        runner.power(f'Runtime checkpoint wake {cycle}', home)
        root = {'foregroundAppId': 'espocket.app.hello', 'pageId': 'root',
                'display': True, 'canBack': False, 'backPending': False}
        runner.touch(f'Native Launcher {cycle}', {**home, 'surface': 'launcher'}, *profile['up'])
        runner.touch(f'Native Root {cycle}', root, profile['native_tap'])
        runner.touch(f'Native Detail {cycle}', {**root, 'pageId': 'detail', 'canBack': True}, profile['detail_tap'])
        runner.power(f'Native Home {cycle}', home)
        runner.power(f'Native resource checkpoint {cycle}', {**home, 'display': False})
        runner.power(f'Native checkpoint wake {cycle}', home)
