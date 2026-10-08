"""Compile the real Shell presentation module; drive its existing public interface."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

OWNER = Path(__file__).resolve().parents[1]


class OverlayPresentationTest(unittest.TestCase):
    def test_continuous_owner_presentation_scenarios(self):
        with tempfile.TemporaryDirectory(prefix='espocket-overlay-module-') as directory:
            binary = Path(directory) / 'test'
            support = OWNER / 'test/support/overlay'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                '-I', str(support), '-I', str(OWNER / 'include'), '-I', str(OWNER / 'src'),
                *[str(OWNER / 'src' / name) for name in (
                    'shell_overlay.cpp', 'shell_keyboard.cpp', 'shell_message_dialog.cpp', 'shell_gesture.cpp')],
                str(support / 'shell_host_fixture.cpp'), str(support / 'scenarios.cpp'),
                '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True, timeout=15)
