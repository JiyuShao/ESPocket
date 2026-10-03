"""Contract between the product theme and pinned official App style consumers."""
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[3]


def style_refs(value):
    if isinstance(value, dict):
        yield from value.get('styleRefs', [])
        for child in value.values():
            yield from style_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from style_refs(child)


class ProductThemeTest(unittest.TestCase):
    def test_official_app_styles_and_visible_control_parts(self):
        required = set()
        required_colors = set()
        for component in ['espressif__brookesia_app_settings', 'espressif__brookesia_app_store']:
            for path in (ROOT / 'firmware/managed_components' / component / 'package/res').rglob('*.json'):
                required.update(style_refs(json.loads(path.read_text())))
                required_colors.update(re.findall(r'\$\{color\.([^}]+)\}', path.read_text()))
        for name in ['dark', 'light']:
            theme = json.loads((ROOT / 'firmware/components/espocket_system/resources' / (name + '_theme.json')).read_text())
            self.assertEqual(theme['id'], name)
            self.assertFalse(required - theme['styles'].keys(), 'official App uses undeclared theme tokens')
            for control in ['app.slider', 'app.switch']:
                style = theme['styles'][control]
                self.assertTrue(style['style']['bgColor'])
                self.assertTrue(style['partStyles']['knob']['bgColor'])
                self.assertTrue(style['partStyles']['indicator'])
            colors = theme['assets'][0]['data']['colors']
            for token in required_colors:
                value = colors
                for key in token.split('.'):
                    self.assertIn(key, value, 'official App uses undeclared color token: ' + token)
                    value = value[key]
                self.assertTrue(value)
            for group, key in [('border', 'default'), ('text', 'default'), ('primary', 'fill')]:
                self.assertTrue(colors[group][key])

    def test_round_layout_keeps_entire_scroll_view_inside_screen(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        original = ROOT / 'firmware/managed_components/espressif__brookesia_app_settings'
        def inside(layout):
            x, y, w, h = (int(layout[k][:-2]) for k in ['pageX', 'pageY', 'pageWidth', 'pageHeight'])
            return all((px-233)**2+(py-233)**2 <= 233**2 for px in [x, x+w] for py in [y, y+h])
        # Original default content rectangle crosses the round viewport.
        baseline = json.loads((original / 'package/res/constants/default.json').read_text())['data']['settings']['layout']
        baseline.update(pageWidth='450dp', pageHeight='404dp')
        self.assertFalse(inside(baseline))
        with tempfile.TemporaryDirectory(prefix='espocket-settings-layout-') as directory:
            patched = prepare(original, ROOT / 'firmware/patches/espressif__brookesia_app_settings/0.8.3/manifest.json', Path(directory) / 'patched')
            variants = json.loads((patched / 'package/res/root.json').read_text())['variants']
            target = variants[-1]
            self.assertEqual(target['when'], '${expr(${env.widthDp} == 466dp && ${env.heightDp} == 466dp)}')
            layout = target['assets'][0]['data']['settings']['layout']
            self.assertTrue(inside(layout), 'content rectangle clips circle corners')
