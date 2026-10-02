"""USB test protocol client; transport is supplied by the caller."""
from __future__ import annotations
import json
import secrets
import time

PREFIX = b'@ESPTEST '
VERSION = 1
CAPABILITIES = {'hello', 'snapshot', 'stimulus.touch', 'stimulus.powerShort', 'release'}


class DeviceTestError(RuntimeError):
    pass


class UsbTestClient:
    def __init__(self, transport, raw_log, *, clock=time.monotonic, sleep=time.sleep,
                 timeout=3.0, request_seed=None):
        self.transport = transport
        self.raw_log = raw_log
        self.clock = clock
        self.sleep = sleep
        self.timeout = timeout
        self.request_id = request_seed if request_seed is not None else secrets.randbits(32) << 16
        self.last_seq = 0
        self.snapshots = []
        self.identity = None

    def request(self, op, **parameters):
        self.request_id += 1
        request = {'version': VERSION, 'request_id': self.request_id, 'op': op, **parameters}
        frame = PREFIX + json.dumps(request, separators=(',', ':')).encode() + b'\n'
        if len(frame.rstrip(b'\n')) > 1024:
            raise DeviceTestError('request exceeds firmware frame limit')
        self.raw_log.write(b'TX ' + frame)
        self.raw_log.flush()
        if self.transport.write(frame) != len(frame):
            raise DeviceTestError('partial request write')
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            line = self.transport.readline(4096)
            if not line:
                continue
            self.raw_log.write(b'RX ' + line)
            self.raw_log.flush()
            if not line.startswith(PREFIX):
                self.check_log(line)
                continue
            try:
                reply = json.loads(line[len(PREFIX):])
            except (ValueError, UnicodeDecodeError) as error:
                raise DeviceTestError('malformed protocol response') from error
            if not isinstance(reply, dict):
                raise DeviceTestError('response must be an object')
            if reply.get('request_id') != self.request_id:
                # Old serial responses cannot satisfy this attempt's fresh request.
                continue
            if reply.get('version') != VERSION or type(reply.get('ok')) is not bool:
                raise DeviceTestError('invalid response envelope')
            if not reply['ok']:
                raise DeviceTestError(f"{op}: {reply.get('error_code', 'missing error code')}")
            return reply
        raise DeviceTestError(f'{op}: response timeout')

    def capture_logs(self, duration):
        """Read a bounded quiet window without adding protocol response traffic."""
        deadline = self.clock() + duration
        while self.clock() < deadline:
            line = self.transport.readline(4096)
            if line:
                self.raw_log.write(b'RX ' + line)
                self.raw_log.flush()
                self.check_log(line)
            else:
                self.sleep(0.01)

    @staticmethod
    def check_log(line):
        markers = (b'A stack overflow in task', b'Guru Meditation', b'panic_abort', b'abort() was called', b'ESP_RST_PANIC',
                   b'Synthetic input tick failed:', b'Input cleanup during stop failed:',
                   b'Synthetic PWR expired', b'Synthetic PWR cancelled',
                   b'USB Test Adapter response write failed', b'ESP-ROM:esp32', b'ESPocket started')
        if any(marker in line for marker in markers):
            raise DeviceTestError('device error observed; see serial.log')

    def hello(self, expected_image=None):
        reply = self.request('hello')
        identity = reply.get('image_identity')
        capabilities = reply.get('capabilities')
        if not isinstance(identity, str) or not identity or not isinstance(capabilities, list) or \
                any(not isinstance(item, str) for item in capabilities):
            raise DeviceTestError('invalid hello identity/capabilities')
        self.identity = {'image_identity': identity, 'protocol_version': VERSION,
                         'capabilities': capabilities}
        if expected_image is not None and identity != expected_image:
            raise DeviceTestError(f'image mismatch: expected {expected_image}, received {identity}')
        if not CAPABILITIES.issubset(capabilities):
            raise DeviceTestError('firmware lacks required capabilities; do not infer support from source')
        return self.identity

    def snapshot(self):
        value = self.request('snapshot').get('snapshot')
        if not isinstance(value, dict):
            raise DeviceTestError('missing snapshot')
        if type(value.get('seq')) is not int or value['seq'] <= self.last_seq:
            raise DeviceTestError('snapshot sequence did not advance; possible device/Adapter restart')
        for field in ('display', 'canBack', 'backPending', 'inputBusy'):
            if type(value.get(field)) is not bool:
                raise DeviceTestError(f'invalid snapshot {field}')
        for field in ('surface', 'foregroundAppId', 'pageId'):
            if not isinstance(value.get(field), str):
                raise DeviceTestError(f'invalid snapshot {field}')
        if value['foregroundAppId'] and not value['pageId']:
            raise DeviceTestError('foreground App without a declared page')
        if not value['foregroundAppId'] and (value['pageId'] or value['canBack'] or value['backPending']):
            raise DeviceTestError('page state without a foreground App')
        if value['backPending'] and value['canBack']:
            raise DeviceTestError('pending Back cannot also accept another Back')
        self.last_seq = value['seq']
        self.snapshots.append(value)
        return value
