"""Configured font fallback and literal UI text must agree before deployment."""
from pathlib import Path
import sys
import os
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from check_glyphs import BuiltinFonts, check, check_document


class GlyphCoverageTest(unittest.TestCase):
    def fonts(self):
        return BuiltinFonts((ROOT / 'firmware/sdkconfig.defaults').read_text())

    def test_real_fallback_reproduces_launcher_rectangle(self):
        bad = {'type': 'label', 'labelProps': {'text': '\uf054'}, 'style': {'fontSize': '16sp'}}
        original = BuiltinFonts('CONFIG_LV_FONT_MONTSERRAT_18=y\nCONFIG_LV_FONT_DEFAULT_UNSCII_8=y\n')
        errors = check_document(bad, {}, original, 'launcher')
        self.assertEqual(len(errors), 1)
        self.assertIn('U+F054 missing from unscii_8', errors[0])
        self.assertEqual(check_document(bad, {}, self.fonts(), 'launcher'), [])
        bad['style']['fontSize'] = '18sp'
        self.assertEqual(check_document(bad, {}, self.fonts(), 'launcher'), [])

    def test_inherited_style_reference_and_unknown_symbol(self):
        node = {'styleRefs': ['caption'], 'children': [
            {'labelProps': {'text': '\uf054'}}, {'labelProps': {'text': '\ue000'}}]}
        errors = check_document(node, {'caption': {'fontSize': '18sp'}}, self.fonts(), 'fixture')
        self.assertEqual(len(errors), 1)
        self.assertIn('U+E000 missing from montserrat_18', errors[0])

    def test_checker_matches_pinned_backend_selection(self):
        source = (ROOT / 'firmware/managed_components/espressif__brookesia_gui_lvgl/src/style_font.cpp').read_text()
        actual = source[source.index('const lv_font_t *get_builtin_font('):source.index('bool node_type_uses_text_font(')]
        harness = '#include <cstdint>\n#include <cassert>\nstruct lv_font_t {int size;};\n'
        for size in self.fonts().sizes:
            harness += f'#define CONFIG_LV_FONT_MONTSERRAT_{size} 1\nlv_font_t lv_font_montserrat_{size}{{{size}}};\n'
        harness += 'lv_font_t fallback{8};\n#define LV_FONT_DEFAULT (&fallback)\n' + actual
        for size in (14, 16, 18, 24, 76):
            font, _ = self.fonts().resolve(size)
            expected = int(font.rsplit('_', 1)[1])
            harness += f'\nstatic const bool verify_{size}=[]{{assert(get_builtin_font({size})->size=={expected}); return true;}}();\n'
        harness += 'int main() {}\n'
        with tempfile.TemporaryDirectory(prefix='espocket-font-selection-') as directory:
            path = Path(directory)/'test.cpp'; path.write_text(harness)
            binary = Path(directory)/'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)

    def test_maintained_resources_have_real_cmap_coverage(self):
        self.assertEqual(check(), [])


if __name__ == '__main__':
    unittest.main()
