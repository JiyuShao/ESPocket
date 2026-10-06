"""Exercise the real CMake staging owner and product resource image gate."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('resource_check', ROOT / 'firmware/main/check_resources.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ResourceIntegrity(unittest.TestCase):
    def test_real_staging_removes_deleted_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cmake = root / 'cmake'
            shutil.copytree(ROOT / 'firmware/managed_components/espressif__brookesia_system_core/cmake', cmake)
            subprocess.run(['patch', '-p1', '-i', str(ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/014-refresh-staged-package.patch')], cwd=root, check=True, capture_output=True)
            source = root / 'input'
            source.mkdir()
            (source / 'keep').write_text('one')
            (source / 'obsolete').write_text('obsolete')
            (root / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(probe NONE)\ninclude("${CMAKE_CURRENT_LIST_DIR}/cmake/runtime_app_stage.cmake")\nbrookesia_stage_runtime_app_package(PACKAGE_ID probe SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}/input" STAGE_ROOT "${CMAKE_BINARY_DIR}/apps" NO_INDEX)\n')
            subprocess.run(['cmake', '-S', str(root), '-B', str(root / 'build')], check=True, capture_output=True)
            build = ['cmake', '--build', str(root / 'build')]
            subprocess.run(build, check=True, capture_output=True)
            (source / 'keep').write_text('two')
            (source / 'obsolete').unlink()
            subprocess.run(build, check=True, capture_output=True)
            self.assertEqual((root / 'build/apps/probe/keep').read_text(), 'two')
            self.assertFalse((root / 'build/apps/probe/obsolete').exists())

    def test_missing_declared_assets_images_and_runtime_entry_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input'
            shutil.copytree(ROOT / 'firmware/runtime_apps/hello/src', source)
            checker.check_package(source, runtime=True)
            import json
            root_document = source / 'res/root.json'
            document = json.loads(root_document.read_text())
            document['assets'].append({'type': 'constant', 'data': {'width': '466dp'}})
            root_document.write_text(json.dumps(document))
            checker.check_package(source, runtime=True)
            for member in ('res/screens/main.json', 'app/main.js', 'res/navigation.json'):
                path = source / member
                original = path.read_bytes()
                path.unlink()
                with self.assertRaises(ValueError):
                    checker.check_package(source, runtime=True)
                path.write_bytes(original)
            image = source / 'res/images'
            image.mkdir()
            (image / 'index.json').write_text('{"type":"imageSet","images":[{"src":"missing.png"}]}')
            (source / 'res/root.json').write_text('{"assets":["images/index.json"]}')
            with self.assertRaises(ValueError):
                checker.check_package(source)

    def test_stale_or_modified_stage_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            staged = Path(directory) / 'staged'
            source = ROOT / 'firmware/runtime_apps/hello/src'
            shutil.copytree(source, staged)
            checker.check_package(source, staged, True)
            (staged / 'obsolete').write_text('old')
            with self.assertRaises(ValueError):
                checker.check_package(source, staged, True)
            (staged / 'obsolete').unlink()
            (staged / 'app/main.js').write_text('old code')
            with self.assertRaises(ValueError):
                checker.check_package(source, staged, True)


if __name__ == '__main__':
    unittest.main()
