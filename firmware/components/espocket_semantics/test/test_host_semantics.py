"""Exercise public semantic declarations and Owner invalidation without IDF."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
COMPONENT = Path(__file__).resolve().parents[1]
class SemanticContractTest(unittest.TestCase):
    def test_owner_lifetime_and_admission(self):
        with tempfile.TemporaryDirectory(prefix="espocket-semantic-") as directory:
            binary = Path(directory) / "contract"
            subprocess.run([os.environ.get("CXX", "clang++"), "-std=c++23", "-pthread",
                            "-I", str(COMPONENT / "include"),
                            str(COMPONENT / "test/test_semantic_contract.cpp"),
                            "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_brightness_results_and_real_caller(self):
        with tempfile.TemporaryDirectory(prefix="espocket-brightness-") as directory:
            binary = Path(directory) / "brightness"
            subprocess.run([os.environ.get("CXX", "clang++"), "-std=c++23", "-pthread",
                            "-I", str(COMPONENT / "include"),
                            str(COMPONENT / "src/brightness.cpp"),
                            str(COMPONENT / "test/test_brightness.cpp"),
                            "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)
