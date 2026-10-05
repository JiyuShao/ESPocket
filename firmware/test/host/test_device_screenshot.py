"""The screenshot Driver rejects corrupted/incomplete device evidence."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('capture_screen', ROOT / 'scripts/firmware/capture_device_screen.py')
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)

class CaptureClient:
    def __init__(self, defect=None):
        self.raw = bytes.fromhex('00f8e0071f00') * 100
        self.defect = defect
    def request(self, op, **parameters):
        if op == 'screenshot':
            return {'screenshot': {'width': 30, 'height': 10, 'size': 600, 'capture_id': 8,
                    'format': 'rgb565le', 'sha256': hashlib.sha256(self.raw).hexdigest()}}
        offset, length = parameters['offset'], parameters['length']
        data = self.raw[offset:offset+length]
        if self.defect == 'corruption':
            data = bytes([data[0] ^ 1]) + data[1:]
        if self.defect == 'truncation':
            data = data[:-1]
        return {'capture_id': 9 if self.defect == 'identity' else 8,
                'offset': offset + 1 if self.defect == 'offset' else offset, 'pixel_hex': data.hex()}

class DeviceScreenshotDriverTest(unittest.TestCase):
    def test_chunks_digest_and_primary_colors(self):
        client = CaptureClient()
        meta, raw = DRIVER.download_frame(client)
        self.assertEqual(raw, client.raw)
        self.assertEqual(meta['capture_id'], 8)
        self.assertEqual(DRIVER.rgb565_to_rgb(bytes.fromhex('00f8e0071f00')), bytes([255,0,0,0,255,0,0,0,255]))
        png = DRIVER.encode_png(3, 1, DRIVER.rgb565_to_rgb(raw[:6]))
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
    def test_corrupted_evidence_is_never_a_successful_capture(self):
        for defect in ['corruption', 'truncation', 'identity', 'offset']:
            with self.subTest(defect=defect), self.assertRaises(DRIVER.DeviceTestError):
                DRIVER.download_frame(CaptureClient(defect))

if __name__ == '__main__':
    unittest.main()
