#!/usr/bin/env python3
"""Capture an immutable RGB565 display frame over the developer USB protocol."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from firmware.test.device.support.usb_test_client import UsbTestClient, DeviceTestError


def download_frame(client, *, chunk_size=512):
    if type(chunk_size) is not int or not 1 <= chunk_size <= 512:
        raise ValueError('chunk_size must be 1..512')
    meta = client.request('screenshot').get('screenshot')
    if not isinstance(meta, dict) or meta.get('format') != 'rgb565le':
        raise DeviceTestError('invalid screenshot metadata')
    width, height, size, capture = (meta.get(k) for k in ('width', 'height', 'size', 'capture_id'))
    if any(type(v) is not int for v in (width, height, size, capture)) or \
            not 0 < width <= 1024 or not 0 < height <= 1024 or size != width * height * 2 or capture <= 0:
        raise DeviceTestError('invalid screenshot dimensions or capture identity')
    raw = bytearray()
    while len(raw) < size:
        offset = len(raw)
        count = min(chunk_size, size - offset)
        reply = client.request('screenshot.read', capture_id=capture, offset=offset, length=count)
        if reply.get('capture_id') != capture or reply.get('offset') != offset:
            raise DeviceTestError('screenshot chunk identity/offset mismatch')
        try:
            data = bytes.fromhex(reply['pixel_hex'])
        except (KeyError, TypeError, ValueError) as error:
            raise DeviceTestError('invalid screenshot pixels') from error
        if len(data) != count:
            raise DeviceTestError('truncated screenshot chunk')
        raw.extend(data)
    if hashlib.sha256(raw).hexdigest() != meta.get('sha256'):
        raise DeviceTestError('screenshot digest mismatch')
    return meta, bytes(raw)


def rgb565_to_rgb(raw):
    rgb = bytearray()
    for (pixel,) in struct.iter_unpack('<H', raw):
        r, g, b = pixel >> 11, (pixel >> 5) & 63, pixel & 31
        rgb.extend(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))
    return bytes(rgb)


def encode_png(width, height, rgb):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\x00' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--expected-image', required=True)
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/espocket-screenshots'))
    args = parser.parse_args()
    # Dependencies are checked before talking to the device.
    import serial
    directory = args.output.resolve() / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + str(uuid.uuid4()))
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    result = {'expected_image': args.expected_image, 'evidence_type': 'rendered-frame',
              'physical_panel_verified': False, 'wake_requested': False}
    with (directory / 'serial.log').open('xb') as log, \
            serial.Serial(args.port, 115200, timeout=.05, write_timeout=1) as port:
        client = UsbTestClient(port, log, timeout=8)
        try:
            result['identity'] = client.hello(args.expected_image)
            if not {'screenshot', 'screenshot.read'}.issubset(result['identity']['capabilities']):
                raise DeviceTestError('image has no screenshot capability')
            meta, raw = download_frame(client)
            (directory / 'screen.png').write_bytes(encode_png(meta['width'], meta['height'], rgb565_to_rgb(raw)))
            (directory / 'screen.rgb565').write_bytes(raw)
            result.update(status='PASS', screenshot=meta, png=str(directory / 'screen.png'))
        except Exception as error:
            result.update(status='FAIL', error=f'{type(error).__name__}: {error}')
        finally:
            try:
                client.request('release')
            except Exception as error:
                result.update(status='FAIL', cleanup_error=str(error))
    (directory / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
