"""Verify the embedded CJK subset with the same outline decoder used on device."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_product_font import repertoire


class ProductFontAssetTest(unittest.TestCase):
    def test_locked_font_covers_repertoire_and_renders_small_and_large_text(self):
        directory = ROOT / 'firmware/components/espocket_system/resources/fonts'
        font = directory / 'espocket_cjk.otf'
        manifest = json.loads((directory / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(font.read_bytes()).hexdigest(), manifest['sha256'])
        self.assertEqual(font.stat().st_size, manifest['bytes'])
        self.assertLess(font.stat().st_size, 1_600_000)
        codepoints = sorted(repertoire())
        self.assertEqual(len(codepoints), manifest['codepoints'])
        decoder = ROOT / 'firmware/managed_components/lvgl__lvgl/src/libs/tiny_ttf'
        code = r'''
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <vector>
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype_htcw.h"
int main(int argc, char **argv) {
    assert(argc == 2);
    auto *input = std::fopen(argv[1], "rb");
    assert(input);
    std::fseek(input, 0, SEEK_END);
    auto length = std::ftell(input);
    std::rewind(input);
    std::vector<unsigned char> data(length);
    assert(std::fread(data.data(), 1, data.size(), input) == data.size());
    std::fclose(input);
    stbtt_fontinfo font{};
    assert(stbtt_InitFont(&font, data.data(), 0));
    const int codepoints[] = {CODEPOINTS};
    for (auto codepoint : codepoints) assert(stbtt_FindGlyphIndex(&font, codepoint) != 0);
    for (auto size : {10, 12, 18, 28, 64}) {
        for (auto codepoint : {0x5317, 0x4eac, 0x6674, 0x6e29, 0x4f60, 0x597d,
                              0x4e00, 0x52a0, 0x7b49, 0x4e8e, 0x51e0, 0x31, 0xb0}) {
            int width = 0, height = 0;
            auto *bitmap = stbtt_GetCodepointBitmap(&font, 0, stbtt_ScaleForPixelHeight(&font, size),
                codepoint, &width, &height, nullptr, nullptr);
            assert(bitmap && width > 0 && height > 0);
            stbtt_FreeBitmap(bitmap, nullptr);
        }
    }
}
'''.replace('CODEPOINTS', ','.join(map(str, codepoints)))
        with tempfile.TemporaryDirectory(prefix='espocket-font-asset-') as temporary:
            source = Path(temporary) / 'font.cpp'
            binary = Path(temporary) / 'font'
            source.write_text(code)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-O2',
                            '-I', str(decoder), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary), str(font)], check=True)


if __name__ == '__main__':
    unittest.main()
