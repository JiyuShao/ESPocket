"""Exercise the locked GUI parser's allocation budget and document compatibility."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_gui_interface'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_gui_interface/0.8.2/manifest.json'
HARNESS = r'''
#include <cstdio>
#include <cstdlib>
#include <new>
#include "brookesia/gui_interface/parser.hpp"
struct alignas(std::max_align_t) Allocation { size_t size; };
size_t live_bytes = 0, peak_bytes = 0, budget_bytes = 0;
void *operator new(size_t size) {
    if (budget_bytes && (live_bytes > budget_bytes || size > budget_bytes - live_bytes))
        throw std::bad_alloc();
    auto *block = static_cast<Allocation *>(std::malloc(sizeof(Allocation) + size));
    if (!block) throw std::bad_alloc();
    block->size = size;
    live_bytes += size;
    peak_bytes = std::max(peak_bytes, live_bytes);
    return block + 1;
}
void operator delete(void *pointer) noexcept {
    if (!pointer) return;
    auto *block = static_cast<Allocation *>(pointer) - 1;
    live_bytes -= block->size;
    std::free(block);
}
void *operator new[](size_t size) { return ::operator new(size); }
void operator delete[](void *pointer) noexcept { ::operator delete(pointer); }
void operator delete(void *pointer, size_t) noexcept { ::operator delete(pointer); }
void operator delete[](void *pointer, size_t) noexcept { ::operator delete(pointer); }
void print_metrics(bool oom) {
    std::printf("{\"peak\":%zu,\"retained\":%zu,\"oom\":%s}\n",
                peak_bytes, live_bytes, oom ? "true" : "false");
}
int main(int argc, char **argv) {
    if (argc != 3) return 3;
    budget_bytes = std::strtoull(argv[2], nullptr, 10);
    try {
        esp_brookesia::gui::Environment environment{.width_px=466, .height_px=466};
        auto result = esp_brookesia::gui::parse_document_file_with_metadata(argv[1], environment);
        budget_bytes = 0;
        print_metrics(false);
        boost::json::value spec;
        if (result) {
            spec = esp_brookesia::lib_utils::describe_to_json(result->document);
            spec.as_object()["constants"] = result->document.constants;
            spec.as_object()["dependency_files"] =
                esp_brookesia::lib_utils::describe_to_json(result->dependency_files);
        } else {
            spec = boost::json::object{{"error", result.error()}};
        }
        const auto output = boost::json::serialize(spec);
        std::puts(output.c_str());
        return result ? 0 : 1;
    } catch (const std::bad_alloc &) {
        budget_bytes = 0;
        print_metrics(true);
        return 2;
    }
}
'''
STORAGE = r'''
#pragma once
#include <expected>
#include <fstream>
#include <iterator>
#include <string>
namespace esp_brookesia::service::helper {
struct Storage {
    static std::expected<std::string, std::string> fs_read_text(const std::string &path) {
        std::ifstream stream(path, std::ios::binary);
        if (!stream) return std::unexpected("missing file: " + path);
        return std::string(std::istreambuf_iterator<char>(stream), {});
    }
};
}
'''


def build(component, directory):
    directory.mkdir()
    shims = directory / 'shims'
    files = {
        'brookesia/service_helper/system/storage.hpp': STORAGE,
        'brookesia/lib_utils/check.hpp': '#pragma once\n',
        'brookesia/lib_utils/log.hpp': '#pragma once\n' + ''.join(
            f'#define {name}(...)\n' for name in [
                'BROOKESIA_LOG_TRACE_GUARD', 'BROOKESIA_LOGD', 'BROOKESIA_LOGI',
                'BROOKESIA_LOGW', 'BROOKESIA_LOGE']),
    }
    for relative, contents in files.items():
        target = shims / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents)
    harness, boost = directory / 'probe.cpp', directory / 'boost.cpp'
    harness.write_text(HARNESS)
    boost.write_text('#include <boost/json/src.hpp>\n')
    components = ROOT / 'firmware/managed_components'
    utils = components / 'espressif__brookesia_lib_utils'
    command = [os.environ.get('CXX', 'clang++'), '-std=c++23', '-O2', '-DBOOST_NO_USER_CONFIG']
    for include in [shims, component / 'include', component / 'src', utils / 'include',
                    components / 'espressif__esp-boost/src']:
        command.extend(['-I', str(include)])
    command.extend(str(component / 'src' / name) for name in [
        'parser.cpp', 'parser_assets.cpp', 'parser_json.cpp', 'parser_node.cpp',
        'parser_style.cpp', 'validator.cpp', 'binding.cpp'])
    binary = directory / 'probe'
    command.extend([str(harness), str(boost), str(utils / 'src/describe_helpers.cpp'), '-o', str(binary)])
    subprocess.run(command, check=True, timeout=180)
    return binary


def fixture():
    leaf = {'type': 'viewTemplate', 'id': 'leaf', 'node': {
        'type': 'label', 'interactionRefs': ['disabled'],
        'labelProps': {'text': 'allocation-fixture-' + 'text-' * 12}}}
    children = [{'type': 'templateRef', 'id': f'leaf_{index}', 'templateId': 'leaf'}
                for index in range(17)]
    branch = {'type': 'viewTemplate', 'id': 'branch',
              'node': {'type': 'container', 'children': children}}
    nested = {'type': 'container', 'id': 'rows', 'children': [
        {'type': 'container', 'id': f'branch_{index}', 'children': copy.deepcopy(children)}
        for index in range(17)] + [
        {'type': 'templateRef', 'id': 'nested_template', 'templateId': 'branch'}]}
    for depth in range(5):
        nested = {'type': 'container', 'id': f'level_{depth}', 'children': [nested]}
    return {'version': '0.1.1', 'assets': [
        {'type': 'constant', 'data': {'marker': 'fixture'}},
        {'type': 'interactionTemplate', 'id': 'disabled',
         'commonProps': {'disabled': True, 'clickable': False}},
        leaf, branch, {'type': 'viewScreen', 'id': 'main', 'children': [nested]}]}


def exercise(binary, source, budget=0):
    result = subprocess.run([str(binary), str(source), str(budget)],
                            capture_output=True, text=True, timeout=15)
    lines = result.stdout.splitlines()
    if result.returncode not in (0, 1, 2) or not lines:
        raise AssertionError(result.stdout + result.stderr)
    metrics = json.loads(lines[0])
    return result.returncode, metrics, lines[1] if len(lines) > 1 else None


class GuiParserAllocationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='espocket-gui-parser-')
        cls.addClassCleanup(temporary.cleanup)
        cls.directory = Path(temporary.name)
        patched = prepare(SOURCE, MANIFEST, cls.directory / 'patched')
        cls.upstream = build(SOURCE, cls.directory / 'upstream-build')
        cls.patched = build(patched, cls.directory / 'patched-build')

    def test_nested_templates_fit_budget_without_changing_expanded_document(self):
        source = self.directory / 'nested.json'
        source.write_text(json.dumps(fixture()))
        status, original, spec = exercise(self.upstream, source)
        self.assertEqual(status, 0)
        status, candidate, candidate_spec = exercise(self.patched, source)
        self.assertEqual(status, 0)
        self.assertEqual(candidate_spec, spec)
        document = json.loads(spec)
        self.assertEqual(document['constants'], {'marker': 'fixture'})
        self.assertEqual(document['templates'][0]['common_props']['disabled'], True)
        budget = original['peak'] * 2 // 3
        status, rejected, rejected_spec = exercise(self.upstream, source, budget)
        self.assertEqual(status, 2)
        self.assertTrue(rejected['oom'])
        self.assertIsNone(rejected_spec)
        status, accepted, accepted_spec = exercise(self.patched, source, budget)
        self.assertEqual(status, 0, accepted)
        self.assertFalse(accepted['oom'])
        self.assertLessEqual(accepted['peak'], budget)
        self.assertEqual(accepted_spec, spec)
        self.assertLessEqual(candidate['retained'], original['retained'] * 2 // 3)

    def test_interaction_reference_success_and_errors_match_upstream(self):
        cases = [
            ({}, None), ({'interactionRefs': []}, None),
            ({'interactionRefs': ['disabled']}, None),
            ({'interactionRefs': 'disabled'}, "Field 'interactionRefs' must be an array"),
            ({'interactionRefs': None}, "Field 'interactionRefs' must be an array"),
            ({'interactionRefs': ['disabled', 1]}, "Field 'interactionRefs' must only contain strings"),
            ({'interactionRefs': ['missing']}, 'Node references missing interactionTemplate: missing'),
            ({'interaction_refs': ['disabled']}, None),
            ({'interaction_refs': 1}, None),
            ({'interactionRefs': 1, 'interaction_refs': []}, "Field 'interactionRefs' must be an array"),
        ]
        for location in ['screen', 'child']:
            for fields, error in cases:
                with self.subTest(location=location, fields=fields):
                    document = fixture()
                    screen = {'type': 'viewScreen', 'id': 'main', 'children': [
                        {'type': 'container', 'id': 'child'}]}
                    target = screen if location == 'screen' else screen['children'][0]
                    target.update(fields)
                    document['assets'][-1] = screen
                    source = self.directory / 'compatibility.json'
                    source.write_text(json.dumps(document))
                    original = exercise(self.upstream, source)
                    candidate = exercise(self.patched, source)
                    self.assertEqual(candidate[0], original[0])
                    self.assertEqual(candidate[2], original[2])
                    self.assertEqual(original[0], 1 if error else 0)
                    parsed = json.loads(original[2])
                    if error:
                        self.assertTrue(parsed['error'].endswith(error), parsed)
                    elif fields.get('interactionRefs') == ['disabled']:
                        node = parsed['screens'][0]
                        if location == 'child':
                            node = node['children'][0]
                        self.assertTrue(node['common_props']['disabled'])
                        self.assertFalse(node['common_props']['clickable'])


if __name__ == '__main__':
    unittest.main()
