"""Compile the production Launcher projection and execute admission/race tests."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
class LauncherProjectionTest(unittest.TestCase):
    def test_real_projection(self):
        with tempfile.TemporaryDirectory(prefix='espocket-launcher-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra', '-Werror',
                            '-I', str(COMPONENT / 'include'), str(COMPONENT / 'src/launcher_projection.cpp'),
                            str(COMPONENT / 'test/test_launcher_projection.cpp'), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)
if __name__ == '__main__': unittest.main()
