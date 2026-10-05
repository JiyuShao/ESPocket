"""Exercise frame assembly and the real protocol without a display or USB."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]

class ScreenshotHostTest(unittest.TestCase):
    def test_frame_and_protocol(self):
        with tempfile.TemporaryDirectory(prefix='espocket-screenshot-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                            '-I', str(COMPONENT / 'include'),
                            *[str(COMPONENT / path) for path in ['src/developer_mode.cpp', 'src/test_protocol.cpp',
                              'src/screenshot.cpp', 'test/test_screenshot.cpp']], '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    unittest.main()
