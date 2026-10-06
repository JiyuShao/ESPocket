"""A blocking HTTP download must leave capacity for progress publication."""
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
spec = importlib.util.spec_from_file_location('patched_builder', ROOT / 'scripts/firmware/build_patched_firmware.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class HttpDownloadProgressTest(unittest.TestCase):
    def test_defaults_and_existing_config_leave_worker_for_progress(self):
        defaults = (ROOT / 'firmware/sdkconfig.defaults').read_text()
        workers = int(re.search(r'^CONFIG_BROOKESIA_SERVICE_HTTP_WORKER_NUM=(\d+)$', defaults, re.M)[1])
        self.assertGreaterEqual(workers, 2)
        configured = builder.configure_audio_candidate('CONFIG_BROOKESIA_SERVICE_HTTP_WORKER_NUM=1\n')
        self.assertIn('CONFIG_BROOKESIA_SERVICE_HTTP_WORKER_NUM=2', configured)
        self.assertNotIn('CONFIG_BROOKESIA_SERVICE_HTTP_WORKER_NUM=1', configured)
        self.assertIn('CONFIG_BROOKESIA_SERVICE_HTTP_MAX_CONCURRENT_REQUESTS=1', configured)
        builder.verify_audio_config(configured)
        with self.assertRaises(ValueError):
            builder.verify_audio_config(configured.replace('HTTP_WORKER_NUM=2', 'HTTP_WORKER_NUM=1'))
