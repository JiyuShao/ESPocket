#!/usr/bin/env python3
"""Check maintained literal labels against configured LVGL built-in font cmaps.

Dynamic text, external Apps and file/image fonts require their own coverage gate.
"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def font_coverage(path):
    source = path.read_text()
    arrays = {}
    for name, body in re.findall(r'static const uint(?:8|16|32)_t (\w+)\[\]\s*=\s*\{(.*?)\};', source, re.S):
        arrays[name] = [int(value, 0) for value in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b', re.sub(r'/\*.*?\*/', '', body, flags=re.S))]
    section = re.search(r'static const lv_font_fmt_txt_cmap_t cmaps\[\]\s*=\s*\{(.*?)\n\};', source, re.S)
    if not section:
        raise ValueError(f'No font cmap: {path}')
    result = set()
    for body in re.findall(r'\{([^{}]+)\}', section[1]):
        fields = dict(re.findall(r'\.(\w+)\s*=\s*([^,\n]+)', body))
        start, count = (int(fields[key].strip(), 0) for key in ('range_start', 'range_length'))
        kind = fields['type'].strip()
        if kind.endswith('FORMAT0_TINY'):
            result.update(range(start, start+count))
        elif kind.endswith('SPARSE_TINY'):
            offsets = arrays[fields['unicode_list'].strip()]
            assert len(offsets) == int(fields['list_length'])
            result.update(start+offset for offset in offsets)
        else:
            raise ValueError(f'Unsupported cmap {kind}: {path}')
    return result


class BuiltinFonts:
    def __init__(self, config, root=ROOT):
        self.sizes = sorted(int(size) for size in re.findall(r'^CONFIG_LV_FONT_MONTSERRAT_(\d+)=y$', config, re.M))
        defaults = re.findall(r'^CONFIG_LV_FONT_DEFAULT_(\w+)=y$', config, re.M)
        if len(defaults) != 1:
            raise ValueError('Declare exactly one CONFIG_LV_FONT_DEFAULT_* in the checked configuration')
        self.default = defaults[0].lower()
        self.directory = root / 'firmware/managed_components/lvgl__lvgl/src/font'
        self.cache = {}

    def resolve(self, size):
        # Pinned GUI get_builtin_font chooses the nearest enabled smaller
        # Montserrat, then LV_FONT_DEFAULT if no smaller size is enabled.
        smaller = [value for value in self.sizes if value <= size]
        name = f'montserrat_{max(smaller)}' if smaller else self.default
        if name not in self.cache:
            self.cache[name] = font_coverage(self.directory / f'lv_font_{name}.c')
        return name, self.cache[name]


def check_document(document, styles, fonts, filename):
    failures = []
    def visit(node, path, inherited=None):
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f'{path}[{index}]', inherited)
        elif isinstance(node, dict):
            style = {}
            for ref in node.get('styleRefs', []):
                style.update(styles[ref])
            style.update(node.get('style', {}))
            size = style.get('fontSize', inherited)
            text = node.get('labelProps', {}).get('text')
            if isinstance(text, str):
                literal = re.sub(r'\$\{[^}]*\}', '', text)
                if literal:
                    match = re.fullmatch(r'(\d+)(?:sp|dp)?', str(size)) if size is not None else None
                    if size is not None and not match:
                        raise ValueError(f'Unresolved fontSize {size}: {filename}:{path}')
                    name, covered = fonts.resolve(int(match[1]) if match else 0)
                    for codepoint in sorted({ord(c) for c in literal if not c.isspace()} - covered):
                        failures.append(f'{filename}:{path}: U+{codepoint:04X} missing from {name} (fontSize={size})')
            for key, child in node.items():
                if key in ('children', 'assets'):
                    visit(child, f'{path}/{node.get("id", key)}', size)
    visit(document, '')
    return failures


def check(root=ROOT, config=None):
    fonts = BuiltinFonts(config if config is not None else (root / 'firmware/sdkconfig.defaults').read_text(), root)
    files = [root / 'firmware/components/shell_circular/resources/gui.json']
    files += sorted((root / 'firmware/native_apps/hello/resources').glob('*.json'))
    files += sorted((root / 'firmware/runtime_apps/hello/src/res').rglob('*.json'))
    failures = []
    for mode in ('light', 'dark'):
        styles = json.loads((root / f'firmware/components/espocket_system/resources/{mode}_theme.json').read_text())['styles']
        for file in files:
            failures += check_document(json.loads(file.read_text()), styles, fonts, f'{file.relative_to(root)} ({mode})')
    return failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdkconfig', type=Path, help='effective firmware configuration; defaults checked otherwise')
    args = parser.parse_args()
    failures = check(config=args.sdkconfig.read_text() if args.sdkconfig else None)
    print('\n'.join(failures) if failures else 'PASS: maintained literal labels have configured built-in glyphs')
    raise SystemExit(bool(failures))
