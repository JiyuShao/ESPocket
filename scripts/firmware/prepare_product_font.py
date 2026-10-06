"""Regenerate the embedded product CJK font from the locked LVGL font source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'firmware/managed_components/lvgl__lvgl/scripts/built_in_font/SourceHanSansSC-Normal.otf'
SOURCE_SHA256 = '1ee89e1669362dee13851129c0a8a791a87521eb4148e5efbf5d26596738e25b'
OUTPUT = ROOT / 'firmware/components/espocket_system/resources/fonts'


def repertoire():
    codepoints = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | {0x2013}
    for high in range(0xA1, 0xF8):
        for low in range(0xA1, 0xFF):
            try:
                codepoints.update(map(ord, bytes([high, low]).decode('gb2312')))
            except UnicodeDecodeError:
                pass
    return codepoints


def main():
    import fontTools
    from fontTools import subset

    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise ValueError('Locked CJK font source changed')
    options = subset.Options()
    options.layout_features = []
    options.hinting = False
    options.recalc_timestamp = False
    font = subset.load_font(str(SOURCE), options)
    font.recalcTimestamp = False
    codepoints = repertoire()
    missing = codepoints - set(font.getBestCmap())
    if missing:
        raise ValueError(f'CJK font source lacks required characters: {sorted(missing)}')
    worker = subset.Subsetter(options=options)
    worker.populate(unicodes=sorted(codepoints))
    worker.subset(font)
    names = {1: 'ESPocket CJK', 2: 'Regular', 3: 'ESPocket CJK Regular',
             4: 'ESPocket CJK Regular', 6: 'ESPocketCJK-Regular',
             16: 'ESPocket CJK', 17: 'Regular'}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    cff = font['CFF '].cff
    cff.fontNames = ['ESPocketCJK-Regular']
    cff.topDictIndex[0].FamilyName = 'ESPocket CJK'
    cff.topDictIndex[0].FullName = 'ESPocket CJK Regular'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / 'espocket_cjk.otf'
    subset.save_font(font, str(target), options)
    (OUTPUT / 'manifest.json').write_text(json.dumps({
        'source': str(SOURCE.relative_to(ROOT)),
        'source_sha256': source_hash,
        'fonttools_version': fontTools.__version__,
        'family': 'ESPocket CJK',
        'repertoire': 'GB2312, printable Latin-1 and en dash',
        'codepoints': len(codepoints),
        'bytes': target.stat().st_size,
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'license': 'SIL Open Font License 1.1',
    }, indent=2) + '\n')
    print(f'Generated {target}: {target.stat().st_size} bytes')


if __name__ == '__main__':
    main()
