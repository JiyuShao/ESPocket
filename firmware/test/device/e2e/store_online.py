"""Real Store online refresh and stop; cached startup alone cannot pass this gate."""
from pathlib import Path
from ..support.usb_test_client import DeviceTestError

INDEX_WRITE = b'Wrote App Store cache file: /littlefs/apps/brookesia.general.app_store/cache/index.json'
STORE = {'foregroundAppId': 'brookesia.general.app_store', 'pageId': 'store.root', 'display': True}
HOME = {'surface': 'watch_face', 'foregroundAppId': '', 'pageId': '', 'display': True}


def run(runner, profile):
    # Real dialogs and service startup can keep the input task busy for longer
    # than the navigation default. Keep this bound local to this scenario.
    previous_timeout = runner.timeout
    runner.timeout = 12
    try:
        initial = runner.snapshot()
        if initial['inputBusy']:
            raise DeviceTestError('device already has an occupied input sequence')
        if not initial['display']:
            runner.power('Store initial wake', {'display': True})
        if initial['foregroundAppId'] or initial['surface'] != 'watch_face':
            runner.power('Store initial Home', HOME)
        runner.touch('Launcher for Store', {**HOME, 'surface': 'launcher'}, *profile['up'])
        runner.stimulate('Store Root', 'stimulus.touch', STORE, quiet_window=8,
                         points=runner.points(profile['store_tap']))
        # Cached-index processing now belongs to the App Owner. Wait for its
        # startup work before requesting the bounded snapshot mailbox.
        runner.capture_logs(12)
        runner.raw_log.flush()
        start = runner.raw_log.tell()
        # Store's modal startup can occupy the App input task longer than the
        # snapshot mailbox deadline. Capture Owner logs before querying it.
        runner.stimulate('Online Store Refresh', 'stimulus.touch', STORE, quiet_window=20,
                         points=runner.points(profile['store_refresh_tap']))
        runner.raw_log.flush()
        # The raw evidence belongs to this immutable attempt. Restrict the
        # positive control to bytes after Refresh, excluding cached startup.
        with Path(runner.raw_log.name).open('rb') as trace:
            trace.seek(start)
            data = trace.read()
        step = {'name': 'Remote index committed after Refresh', 'operation': 'observe-owner-log',
                'status': 'FAIL', 'cachedStartupCanPass': False}
        runner.steps.append(step)
        if INDEX_WRITE not in data:
            raise DeviceTestError('Store Refresh did not commit an online index; see serial.log')
        if b'Too many concurrent HTTP requests' in data:
            raise DeviceTestError('Store discarded a request under HTTP capacity pressure; see serial.log')
        step['status'] = 'PASS'
        runner.power('Store PWR Home', HOME)
        runner.observe('Store stays stopped', HOME, duration=1)
        runner.touch('Launcher after Store stop', {**HOME, 'surface': 'launcher'}, *profile['up'])
        runner.stimulate('Store reopens after HTTP stop', 'stimulus.touch', STORE, quiet_window=8,
                         points=runner.points(profile['store_tap']))
        runner.power('Reopened Store PWR Home', HOME)
    finally:
        runner.timeout = previous_timeout
