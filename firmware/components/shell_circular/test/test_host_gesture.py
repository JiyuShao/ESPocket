"""Exercise the shared Shell input arbiter without LVGL or ESP-IDF."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class ShellGestureHostTest(unittest.TestCase):
    def test_shared_gesture_arbitration(self):
        with tempfile.TemporaryDirectory(prefix='espocket-gesture-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-I', str(COMPONENT / 'include'),
                str(COMPONENT / 'src/shell_gesture.cpp'),
                str(COMPONENT / 'test/test_shell_gesture.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
