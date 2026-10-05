"""Patch preparation must fail closed and leave upstream sources untouched."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    'prepare_patched_component', ROOT / 'scripts/firmware/prepare_patched_component.py')
PATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCHER)


class PatchedComponentTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'upstream'
        self.source.mkdir()
        (self.source / 'source.txt').write_text('first\noriginal\nlast\n')
        (self.source / 'idf_component.yml').write_text('version: 0.8.3\n')
        self.patch = self.root / '001.patch'
        self.patch.write_text(
            '--- a/source.txt\n+++ b/source.txt\n@@ -1,3 +1,3 @@\n'
            ' first\n-original\n+patched\n last\n')
        self.manifest = self.root / 'manifest.json'
        self.output = self.root / 'build/component'
        self.save_manifest()

    def save_manifest(self):
        self.manifest.write_text(json.dumps({
            'schema_version': 1, 'source_files': PATCHER.inventory(self.source),
            'patches': [{'file': self.patch.name, 'sha256': PATCHER.digest(self.patch)}],
        }))

    def test_prepares_copy_and_preserves_upstream(self):
        before = PATCHER.inventory(self.source)
        PATCHER.prepare(self.source, self.manifest, self.output)
        self.assertEqual((self.output / 'source.txt').read_text(), 'first\npatched\nlast\n')
        self.assertEqual(PATCHER.inventory(self.source), before)

    def test_new_file_after_existing_file_is_exact_and_source_is_preserved(self):
        self.patch.write_text(self.patch.read_text() +
            '--- /dev/null\n+++ b/src/new.cpp\n@@ -0,0 +1,2 @@\n+first\n+second\n')
        self.save_manifest()
        PATCHER.prepare(self.source, self.manifest, self.output)
        self.assertEqual((self.output / 'src/new.cpp').read_text(), 'first\nsecond\n')
        self.assertFalse((self.source / 'src').exists())

    def test_new_file_rejects_existing_target_escape_and_bad_coordinates(self):
        for name, coords, content in (
            ('source.txt', '-0,0 +1,1', '+x\n'),
            ('../escape', '-0,0 +1,1', '+x\n'),
            ('new.txt', '-1,0 +1,1', '+x\n'),
            ('new.txt', '-0,1 +1,1', '+x\n'),
            ('new.txt', '-0,0 +2,1', '+x\n'),
            ('new.txt', '-0,0 +1,2', '+x\n'),
        ):
            with self.subTest(name=name, coords=coords):
                self.patch.write_text(f'--- /dev/null\n+++ b/{name}\n@@ {coords} @@\n{content}')
                self.save_manifest()
                with self.assertRaises(ValueError):
                    PATCHER.prepare(self.source, self.manifest, self.output)
                self.assertFalse(self.output.exists())

    def test_changed_added_and_missing_source_files_are_rejected(self):
        for mode in ('changed', 'added', 'missing'):
            with self.subTest(mode=mode):
                extra = self.source / 'extra.txt'
                source = self.source / 'source.txt'
                if mode == 'changed':
                    source.write_text('changed\n')
                elif mode == 'added':
                    extra.write_text('unexpected\n')
                else:
                    source.unlink()
                with self.assertRaisesRegex(ValueError, 'inventory/hash'):
                    PATCHER.prepare(self.source, self.manifest, self.output)
                self.assertFalse(self.output.exists())
                source.write_text('first\noriginal\nlast\n')
                extra.unlink(missing_ok=True)

    def test_patch_tampering_and_context_offset_are_rejected(self):
        self.patch.write_text(self.patch.read_text().replace('original', 'wrong'))
        with self.assertRaisesRegex(ValueError, 'Patch hash'):
            PATCHER.prepare(self.source, self.manifest, self.output)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'context mismatch'):
            PATCHER.prepare(self.source, self.manifest, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.output.parent.glob('.patch-stage-*')))

    def test_no_offset_search(self):
        (self.source / 'source.txt').write_text('extra\nfirst\noriginal\nlast\n')
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'context mismatch'):
            PATCHER.prepare(self.source, self.manifest, self.output)

    def test_source_nested_and_existing_outputs_are_rejected(self):
        for output in (self.source, self.source / 'child', self.root):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, 'separate'):
                    PATCHER.prepare(self.source, self.manifest, output)
        self.output.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            PATCHER.prepare(self.source, self.manifest, self.output)

    def test_output_cannot_target_dependency_cache(self):
        with self.assertRaisesRegex(ValueError, 'managed_components'):
            PATCHER.prepare(self.source, self.manifest, self.root / 'managed_components/copy')

    def test_symlinks_and_path_escape_are_rejected(self):
        (self.source / 'link').symlink_to(self.source / 'source.txt')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            PATCHER.prepare(self.source, self.manifest, self.output)
        for name in ('../escape', '/absolute'):
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                PATCHER.relative_path(name)

    def test_applies_ordered_patches_and_rejects_reversed_order(self):
        second = self.root / '002.patch'
        second.write_text(self.patch.read_text().replace('original', 'patched').replace('+patched', '+final'))
        data = json.loads(self.manifest.read_text())
        data['patches'].append({'file': second.name, 'sha256': PATCHER.digest(second)})
        self.manifest.write_text(json.dumps(data))
        PATCHER.prepare(self.source, self.manifest, self.output)
        self.assertEqual((self.output / 'source.txt').read_text(), 'first\nfinal\nlast\n')
        data['patches'].reverse()
        self.manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'context mismatch'):
            PATCHER.prepare(self.source, self.manifest, self.root / 'reversed')
