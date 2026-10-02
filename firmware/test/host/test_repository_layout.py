"""Cross-component constraints on versioned firmware material."""

from pathlib import Path, PurePosixPath
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]


def generated_paths(paths):
    forbidden = []
    for name in paths:
        path = PurePosixPath(name)
        parts = path.parts
        if not parts or parts[0] != 'firmware':
            continue
        generated = (
            parts[:2] in [('firmware', 'build'), ('firmware', 'managed_components'), ('firmware', 'littlefs')]
            or parts[:3] == ('firmware', 'components', 'gen_bmgr_codes')
            or name in ['firmware/sdkconfig', 'firmware/sdkconfig.old']
            or (len(parts) >= 4 and parts[1] in ['apps', 'runtime_apps', 'native_apps']
                and parts[3] in ['build', 'dist', 'node_modules'])
        )
        if generated:
            forbidden.append(name)
    return forbidden


class RepositoryLayoutTest(unittest.TestCase):
    def test_no_generated_material_is_versioned(self):
        result = subprocess.run(['git', 'ls-files', '-z', '--', 'firmware'],
                                cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(generated_paths(result.stdout.split('\0')), [])

    def test_generated_boundary_covers_current_and_target_layouts(self):
        generated = [
            'firmware/build/espocket.bin',
            'firmware/managed_components/vendor/source.cpp',
            'firmware/components/gen_bmgr_codes/CMakeLists.txt',
            'firmware/sdkconfig', 'firmware/sdkconfig.old',
            'firmware/apps/hello/build/app.js',
            'firmware/runtime_apps/hello/dist/app.pkg',
            'firmware/runtime_apps/hello/node_modules/library/index.js',
        ]
        source = ['firmware/dependencies.lock', 'firmware/sdkconfig.defaults',
                  'firmware/components/espocket_system/src/system.cpp',
                  'firmware/runtime_apps/hello/package.json']
        self.assertEqual(generated_paths(generated + source), generated)

    def test_build_inputs_and_warning_scope(self):
        cmake = (ROOT / 'firmware/CMakeLists.txt').read_text()
        self.assertNotIn('idf_build_set_property(COMPILE_OPTIONS', cmake)
        self.assertEqual(cmake.count('-Wno-error=attributes'), 1)
        self.assertIn('${brookesia_hal_custom_lib} PRIVATE', cmake)
        main = (ROOT / 'firmware/main/CMakeLists.txt').read_text()
        self.assertIn('${CMAKE_BINARY_DIR}/littlefs-root', main)
        paths = (ROOT / 'firmware/components/espocket_system/project_include.cmake').read_text()
        self.assertIn('brookesia_system_core_set_esp_runtime_paths(', paths)
        self.assertIn('INTERNAL_ROOT "/littlefs"', paths)

    def test_tests_live_with_their_owner(self):
        for directory in [*(ROOT / 'firmware/components').iterdir(),
                          *(ROOT / 'firmware/native_apps').iterdir(),
                          *(ROOT / 'firmware/runtime_apps').iterdir()]:
            self.assertFalse((directory / 'tests').exists(),
                             f'{directory.name}: use test/ instead of tests/')
        self.assertFalse((ROOT / 'firmware/tests').exists())
        self.assertFalse((ROOT / 'firmware/components/app_hello').exists())
        self.assertFalse((ROOT / 'firmware/apps').exists())
        self.assertFalse((ROOT / 'firmware/littlefs').exists())
        self.assertFalse((ROOT / 'firmware/components/espocket_system/Kconfig.projbuild').exists())


if __name__ == '__main__':
    unittest.main()
