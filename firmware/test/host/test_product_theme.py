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
            for control in ['button', 'app.primaryChip', 'app.secondaryChip', 'app.buttonPrimary', 'app.buttonSecondary']:
                style = theme['styles'][control]
                self.assertTrue(style['bgColor'])
                self.assertTrue(style['textColor'])
                self.assertTrue(style['stateStyles']['pressed']['bgColor'])
            self.assertEqual(theme['styles']['app.selectableLabelSelected']['textColor'], '${color.primary.on}')
            for control in ['app.slider', 'app.switch']:
                style = theme['styles'][control]
                self.assertTrue(style['bgColor'])
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

    def test_shell_surfaces_use_complete_theme_references(self):
        shell = json.loads((ROOT / 'firmware/components/shell_circular/resources/gui.json').read_text())
        refs = set(style_refs(shell))
        self.assertTrue(refs)
        def check(node):
            if isinstance(node, dict):
                self.assertFalse({'bgColor', 'textColor'} & node.get('style', {}).keys(),
                                 'Shell colors must be owned by the product theme')
                for value in node.values():
                    check(value)
            elif isinstance(node, list):
                for value in node:
                    check(value)
        check(shell)
        for name in ['dark', 'light']:
            theme = json.loads((ROOT / f'firmware/components/espocket_system/resources/{name}_theme.json').read_text())
            self.assertFalse(refs - theme['styles'].keys())
            for asset in shell['assets']:
                if asset.get('type') == 'viewScreen' and 'styleRefs' in asset:
                    colors = [theme['styles'][ref].get('bgColor') for ref in asset['styleRefs']]
                    if name == 'light':
                        token = {'battery_card': 'success.soft', 'brightness_card': 'warning.soft'}.get(asset['id'], 'bg.quick' if asset['id'] == 'quick_settings' else 'bg.base')
                        self.assertIn('${color.' + token + '}', colors)

    def test_compact_quick_controls_fit_round_viewport(self):
        shell = json.loads((ROOT / 'firmware/components/shell_circular/resources/gui.json').read_text())
        quick = next(asset for asset in shell['assets'] if asset['id'] == 'quick_settings')
        controls = [child for child in quick['children'] if child['type'] == 'button']
        self.assertEqual(len(controls), 4)
        for child in controls:
            rect = child['placement']
            x, y, w, h = (int(rect[key][:-2]) for key in ('x', 'y', 'width', 'height'))
            self.assertGreaterEqual(min(w, h), 48)
            for px in (x, x+w):
                for py in (y, y+h):
                    self.assertLessEqual((px-233)**2+(py-233)**2, 233**2)

    def test_reference_app_cards_declare_theme_colors(self):
        paths = ['firmware/native_apps/hello/resources/card.json',
                 'firmware/runtime_apps/hello/src/res/cards.json']
        for relative in paths:
            resource = json.loads((ROOT / relative).read_text())
            refs = set(style_refs(resource))
            self.assertTrue({'app.page', 'app.action', 'app.actionText'} <= refs)
            for name in ['dark', 'light']:
                theme = json.loads((ROOT / f'firmware/components/espocket_system/resources/{name}_theme.json').read_text())
                self.assertFalse(refs - theme['styles'].keys())

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


class ThemeMigrationTest(unittest.TestCase):
    def test_theme_normal_styles_use_the_flat_gui_schema(self):
        # GUI parse_style_set_object passes the theme entry itself to
        # parse_style_object; unlike view assets, nested "style" is ignored.
        for mode in ('light', 'dark'):
            theme = json.loads((ROOT / f'firmware/components/espocket_system/resources/{mode}_theme.json').read_text())
            for name, style in theme['styles'].items():
                self.assertNotIn('style', style, f'{mode}/{name}: normal state is ignored by GUI')
            self.assertEqual(theme['styles']['app.action']['bgColor'], '${color.primary.fill}')

    def test_maintained_pages_and_overlays_use_declared_theme_tokens(self):
        paths = [ROOT / 'firmware/components/shell_circular/resources/gui.json']
        paths += list((ROOT / 'firmware/native_apps/hello/resources').glob('*.json'))
        paths += list((ROOT / 'firmware/runtime_apps/hello/src/res').rglob('*.json'))
        refs = set()
        for path in paths:
            source = path.read_text()
            refs.update(style_refs(json.loads(source)))
            self.assertNotRegex(source, r'"(?:bgColor|textColor|borderColor)"\s*:\s*"#')
            self.assertNotRegex(source, r'shell\.(?:bgColor|textColor)\.')
        native_tokens = set()
        for path in (ROOT / 'firmware/components/shell_circular/src').glob('*.cpp'):
            source = path.read_text()
            self.assertNotRegex(source, r'lv_color_hex\(0x')
            native_tokens.update(re.findall(r'theme_color\("([^"\n]+)"\)', source))
        native_tokens.update(['danger.fill', 'danger.on', 'primary.fill', 'primary.on'])
        for mode in ('light', 'dark'):
            theme = json.loads((ROOT / f'firmware/components/espocket_system/resources/{mode}_theme.json').read_text())
            self.assertFalse(refs - theme['styles'].keys())
            colors = theme['assets'][0]['data']['colors']
            tokens = native_tokens | set(re.findall(r'\$\{color\.([^}]+)\}', json.dumps(theme['styles'])))
            for token in tokens:
                value = colors
                for key in token.split('.'):
                    self.assertIn(key, value, f'{mode}: missing {token}')
                    value = value[key]
                self.assertRegex(value, r'^#[0-9a-fA-F]{6}$')

    def test_theme_text_pairs_have_readable_contrast(self):
        def luminance(color):
            channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(v * weight for v, weight in zip(channels, (.2126, .7152, .0722)))
        for mode in ('light', 'dark'):
            colors = json.loads((ROOT / f'firmware/components/espocket_system/resources/{mode}_theme.json').read_text())['assets'][0]['data']['colors']
            pairs = [(colors['text'][text], colors[group][background])
                     for text in ('default', 'muted', 'subtle')
                     for group, background in [('bg', 'base'), ('bg', 'quick'), ('surface', 'raised')]]
            pairs += [(colors[role]['on'], colors[role]['fill']) for role in ('primary', 'danger', 'warning')]
            pairs += [(colors[role]['fill'], colors[role]['soft']) for role in ('success', 'warning')]
            for foreground, background in pairs:
                a, b = sorted([luminance(foreground), luminance(background)])
                self.assertGreaterEqual((b + .05) / (a + .05), 4.5, f'{mode}: {foreground} on {background}')
