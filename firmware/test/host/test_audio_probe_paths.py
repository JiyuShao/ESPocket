"""Each prepared probe has its own path; old unknown files stay untouched."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_audio_playback_probe import copy_fixture


class AudioProbePathsTest(unittest.TestCase):
    def test_path_and_uri_match_and_builds_are_distinct(self):
        source = ROOT / 'firmware/test/device/fixtures/audio_playback_probe.hpp'
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            targets = [Path(directory) / name for name in ['a.hpp', 'b.hpp']]
            paths = [copy_fixture(source, target) for target in targets]
            self.assertNotEqual(paths[0], paths[1])
            for path, target in zip(paths, targets):
                text = target.read_text()
                self.assertIn('"' + path + '"', text)
                self.assertIn('"file:/' + path + '"', text)
                self.assertNotIn('.espocket-audio-probe-v2.wav', text)
            with self.assertRaises(ValueError):
                copy_fixture(source, targets[0], '../invalid')
        self.assertEqual(source.read_bytes(), before)
