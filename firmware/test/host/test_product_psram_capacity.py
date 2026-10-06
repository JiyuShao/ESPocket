"""Product staging must retain PSRAM capacity for GUI, packages and the VM."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from build_patched_firmware import configure_audio_candidate, verify_audio_config


class ProductPsramCapacityTest(unittest.TestCase):
    def test_board_and_old_config_cannot_reserve_instruction_heap(self):
        options = ('CONFIG_SPIRAM_XIP_FROM_PSRAM', 'CONFIG_SPIRAM_FETCH_INSTRUCTIONS', 'CONFIG_SPIRAM_RODATA')
        defaults = (ROOT / 'firmware/sdkconfig.defaults').read_text().splitlines()
        for option in options:
            self.assertIn(option + '=n', defaults)
        configured = configure_audio_candidate('\n'.join(option + '=y' for option in options))
        verify_audio_config(configured)
        for option in options:
            self.assertIn('# ' + option + ' is not set', configured.splitlines())
            with self.assertRaises(ValueError):
                verify_audio_config(configured.replace('# ' + option + ' is not set', option + '=y'))
