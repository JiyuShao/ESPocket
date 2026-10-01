"""Execute the Navigator contract tests without ESP-IDF or a device."""

from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class NavigatorHostTest(unittest.TestCase):
    def test_navigation_contract(self):
        with tempfile.TemporaryDirectory(prefix='espocket-navigation-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([
                'clang++', '-std=c++23', '-pthread', '-I', str(COMPONENT / 'include'),
                str(COMPONENT / 'src/page_navigator.cpp'),
                str(COMPONENT / 'test/test_page_navigator.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
