"""Navigation hints must use glyphs in the actual built-in font selection."""
import ast
import json
from pathlib import Path
import re
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
ROOT = COMPONENT.parents[2]


def glyphs(size):
    source = (ROOT / 'firmware/managed_components/lvgl__lvgl/src/font' /
              f'lv_font_montserrat_{size}.c').read_text()
    sparse = re.search(r'unicode_list_1\[\] = \{(.*?)\};', source, re.S).group(1)
    ranges = re.findall(r'\.range_start = (\d+), \.range_length = (\d+)', source)
    start, length = map(int, ranges[0])
    sparse_start = int(ranges[1][0])
    return set(range(start, start + length)) | {
        sparse_start + int(value, 16) for value in re.findall(r'0x[0-9a-f]+', sparse)
    }


def nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from nodes(value)


class NavigationGlyphTest(unittest.TestCase):
    def test_navigation_feedback_has_real_font_glyphs(self):
        defaults = (ROOT / 'firmware/sdkconfig.defaults').read_text()
        enabled = sorted(map(int, re.findall(r'^CONFIG_LV_FONT_MONTSERRAT_(\d+)=y$', defaults, re.M)))
        document = json.loads((COMPONENT / 'resources/gui.json').read_text())
        hints = [n for n in nodes(document) if n.get('id') in ('pull_hint', 'hint')]
        self.assertEqual(len(hints), 4)
        for hint in hints:
            size = int(hint['style']['fontSize'].removesuffix('sp'))
            available = [s for s in enabled if s <= size]
            # Smaller than every configured font falls back to UNSCII, which has no arrow symbols.
            self.assertTrue(available, f'{hint["id"]}: no configured text font for {size}sp')
            supported = glyphs(max(available))
            for char in hint['labelProps']['text']:
                self.assertIn(ord(char), supported, f'{hint["id"]}: missing U+{ord(char):04X}')
        symbols = (ROOT / 'firmware/managed_components/lvgl__lvgl/src/font/lv_symbol_def.h').read_text()
        source = (COMPONENT / 'src/circular_shell.cpp').read_text()
        pull = next(h for h in hints if h['id'] == 'pull_hint')
        supported = glyphs(max(s for s in enabled if s <= int(pull['style']['fontSize'][:-2])))
        for line in source.splitlines():
            if not any(text in line for text in ('Keep pulling', 'Release for Home', 'Pull for Home')):
                continue
            texts = re.findall(r'"(?:[^"\\]|\\.)*"', line)
            text = ''.join(ast.literal_eval(t) for t in texts)
            if 'LV_SYMBOL_DOWN' in line:
                literal = re.search(r'^#define LV_SYMBOL_DOWN\s+("[^\n]+?")', symbols, re.M).group(1)
                text = ast.literal_eval(literal).encode('latin1').decode('utf-8') + text
            for char in text:
                self.assertIn(ord(char), supported, f'pull feedback: missing U+{ord(char):04X}')


if __name__ == '__main__':
    unittest.main()
