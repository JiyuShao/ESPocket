"""Execute USB protocol and Developer Mode contracts without hardware."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class ProtocolHostTest(unittest.TestCase):
    def test_developer_mode_and_protocol(self):
        with tempfile.TemporaryDirectory(prefix='espocket-protocol-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-I', str(COMPONENT / 'include'),
                str(COMPONENT / 'src/developer_mode.cpp'),
                str(COMPONENT / 'src/test_protocol.cpp'),
                str(COMPONENT / 'src/power_input_queue.cpp'),
                str(COMPONENT / 'test/test_test_protocol.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
