"""Structural checks for the System/Shell ownership seam."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class OwnerBoundariesTest(unittest.TestCase):
    def test_shell_host_only_exposes_product_semantics(self):
        header = (ROOT / 'firmware/components/shell_circular/include/espocket/circular_shell.hpp').read_text()
        host = re.search(r'struct ShellHost \{(.*?)\n};', header, re.DOTALL).group(1)
        for hardware in ['gpio', 'PowerKey', 'press_count', 'lv_obj', 'ServiceBinding', 'ServiceManager']:
            self.assertNotIn(hardware, host)
        self.assertNotIn('virtual ', host)

    def test_system_is_the_only_power_event_consumer(self):
        shell = ROOT / 'firmware/components/shell_circular'
        for path in [*shell.glob('src/*'), *shell.glob('include/espocket/*')]:
            if path.is_file():
                source = path.read_text()
                self.assertNotIn('power_press_count', source)
                self.assertNotIn('power_handler_', source)
                self.assertNotIn('take_short_press', source)
        system = (ROOT / 'firmware/components/espocket_system/src/system_power.cpp').read_text()
        self.assertIn('power_key_monitor_->take_short_press()', system)
        self.assertIn('handle_power_short_press();', system)
        self.assertIn('stopping_.load', system)


if __name__ == '__main__':
    unittest.main()
