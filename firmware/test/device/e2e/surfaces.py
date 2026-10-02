"""Remaining system Surface paths on the ordinary Circular Shell image."""


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
    for label, surface, direction in (
        ('Battery', 'shell.battery', 'right'), ('Brightness', 'shell.brightness', 'left'),
    ):
        card = {**home, 'surface': surface}
        runner.touch(label + ' Card', card, *profile[direction])
        runner.touch(label + ' outward boundary', card, *profile[direction])
        runner.observe(label + ' boundary does not loop', card)
        runner.power(label + ' PWR Home', home)
    runner.touch('Quick Settings', {**home, 'surface': 'quick_settings'}, *profile['down'])
    runner.power('Quick Settings PWR Home', home)
    runner.touch('Quick Settings for Settings', {**home, 'surface': 'quick_settings'}, *profile['down'])
    runner.touch('Quick Settings opens Settings Root',
                  {'foregroundAppId': 'brookesia.general.settings', 'pageId': 'settings.root',
                   'display': True, 'canBack': False, 'backPending': False}, profile['quick_settings_app_tap'])
    runner.power('Settings PWR Home', home)
    runner.touch('Launcher', {**home, 'surface': 'launcher'}, *profile['up'])
    runner.power('Launcher PWR Home', home)
    runner.touch('Launcher for App swipe', {**home, 'surface': 'launcher'}, *profile['up'])
    root = {'foregroundAppId': 'espocket.app.hello', 'pageId': 'root', 'display': True,
            'canBack': False, 'backPending': False}
    detail = {**root, 'pageId': 'detail', 'canBack': True}
    runner.touch('Native Root', root, profile['native_tap'])
    runner.touch('Native Detail', detail, profile['detail_tap'])
    runner.touch('Native normal horizontal stays Detail', detail, *profile['app_horizontal'])
    runner.observe('Native ordinary swipe cannot Back', detail)
    runner.power('Native Detail PWR Home', home)
