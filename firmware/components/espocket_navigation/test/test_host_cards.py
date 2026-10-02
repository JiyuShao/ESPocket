"""Execute the actual Card Registry's identity and migration contracts."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class CardRegistryHostTest(unittest.TestCase):
    def test_configuration_and_migration(self):
        with tempfile.TemporaryDirectory(prefix='espocket-card-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-I', str(COMPONENT / 'include'),
                str(COMPONENT / 'src/page_navigator.cpp'), str(COMPONENT / 'src/card_registry.cpp'),
                str(COMPONENT / 'test/test_card_registry.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)

    def test_visible_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='espocket-card-session-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-I', str(COMPONENT / 'include'),
                str(COMPONENT / 'src/page_navigator.cpp'), str(COMPONENT / 'src/card_registry.cpp'),
                str(COMPONENT / 'src/card_session.cpp'), str(COMPONENT / 'test/test_card_session.cpp'),
                '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
