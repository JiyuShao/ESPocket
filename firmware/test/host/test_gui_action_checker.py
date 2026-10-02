"""The shared GUI contract checker rejects missing and extra actions."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from gui_actions import validate_action_contract


class GuiActionCheckerTest(unittest.TestCase):
    def test_missing_and_extra_declarations_subscriptions_and_handlers(self):
        component = ROOT / 'firmware/native_apps/hello'
        original = (component / 'src/hello_app.cpp').read_text()
        document = json.loads((component / 'resources/gui.json').read_text())
        with tempfile.TemporaryDirectory(prefix='espocket-gui-contract-') as directory:
            temporary = Path(directory)
            (temporary / 'resources').mkdir()
            (temporary / 'src').mkdir()
            cases = [
                original.replace('for (const auto action : {INCREMENT_ACTION,',
                                 'for (const auto action : {OPEN_DETAIL_ACTION,'),
                original.replace('action != INCREMENT_ACTION', 'action != OPEN_DETAIL_ACTION'),
                original.replace('constexpr std::string_view INCREMENT_ACTION = "hello.increment";',
                                 'constexpr std::string_view INCREMENT_ACTION = "hello.extra";'),
            ]
            for source in cases:
                with self.subTest(source=source):
                    self.assertNotEqual(source, original, 'negative fixture must mutate the source')
                    (temporary / 'src/hello_app.cpp').write_text(source)
                    (temporary / 'resources/gui.json').write_text(json.dumps(document))
                    with self.assertRaises(ValueError):
                        validate_action_contract(temporary, 'hello_app.cpp', 'HelloApp')
            (temporary / 'src/hello_app.cpp').write_text(original)
            # An event with no subscription or handler must also be rejected.
            document['assets'][0]['events'] = [{'type': 'clicked', 'action': 'hello.extra'}]
            (temporary / 'resources/gui.json').write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                validate_action_contract(temporary, 'hello_app.cpp', 'HelloApp')


if __name__ == '__main__':
    unittest.main()
