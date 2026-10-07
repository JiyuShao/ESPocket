"""Parse maintained round documents and check original controller paths and circle bounds."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare
from test_gui_parser_allocation import build, exercise

RESOURCES = ROOT / 'firmware/components/espocket_system/resources'


def walk(node, prefix=''):
    path = prefix + '/' + node.get('id', '')
    yield path, node
    for child in node.get('children', []):
        yield from walk(child, path)


class RoundAppDocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='round-app-documents-')
        cls.addClassCleanup(temporary.cleanup)
        cls.directory = Path(temporary.name)
        component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_gui_interface',
                            ROOT / 'firmware/patches/espressif__brookesia_gui_interface/0.8.2/manifest.json',
                            cls.directory / 'interface')
        cls.binary = build(component, cls.directory / 'parser')

    def test_chat_document_parses_and_preserves_controller_targets(self):
        document = json.loads((RESOURCES / 'chat_round.json').read_text())
        fixtures = {
            'constants/default.json': {'type': 'constant', 'data': {}},
            'i18n/en.json': {'type': 'constant', 'data': {}},
            'images/index.json': {'type': 'imageSet', 'images': [
                {'id': 'nav.chat', 'src': 'chat.png', 'width': 42, 'height': 42},
                {'id': 'nav.settings', 'src': 'settings.png', 'width': 42, 'height': 42}]},
            'flows/ai_chatbot.json': {'type': 'screenFlow', 'id': 'ai_chatbot', 'initial': 'ai_chatbot_chat',
                                    'screens': ['ai_chatbot_chat', 'ai_chatbot_settings', 'ai_chatbot_select'], 'transitions': []},
            'flows/chrome.json': {'type': 'screenFlow', 'id': 'ai_chatbot_chrome', 'initial': 'ai_chatbot_chrome',
                                 'screens': ['ai_chatbot_chrome'], 'transitions': []},
        }
        for relative, asset in fixtures.items():
            path = self.directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asset))
        source = self.directory / 'chat.json'
        source.write_text(json.dumps(document))
        status, metrics, spec = exercise(self.binary, source)
        self.assertEqual(status, 0, spec)
        parsed = json.loads(spec)
        paths = {path: node for screen in parsed['screens'] for path, node in walk(screen)}
        for path in [
            '/ai_chatbot_chat/content/chat_panel/list/items', '/ai_chatbot_chat/content/empty_state/message',
            '/ai_chatbot_chat/content/empty_state/status_chip_network/status_value',
            '/ai_chatbot_chat/content/empty_state/status_chip_agent/status_value',
            '/ai_chatbot_chat/content/empty_state/status_chip_cloud/status_value',
            '/ai_chatbot_chrome/title', '/ai_chatbot_chrome/status', '/ai_chatbot_chrome/clear',
            '/ai_chatbot_chrome/chat/icon', '/ai_chatbot_chrome/chat/label',
            '/ai_chatbot_chrome/settings/icon', '/ai_chatbot_chrome/settings/label',
            '/ai_chatbot_settings/content/agent/value', '/ai_chatbot_settings/content/status/value',
            '/ai_chatbot_select/list_card/list', '/ai_chatbot_select/list_card/empty_state/message',
        ]:
            self.assertIn(path, paths)
        events = {event['action'] for node in paths.values() for event in node.get('events', [])}
        events.update(event['action'] for asset in document['assets'] if isinstance(asset, dict)
                      for _, node in walk(asset.get('node', asset)) for event in node.get('events', []))
        self.assertTrue({'ai_chatbot.history.clear', 'ai_chatbot.chat.open.chat', 'ai_chatbot.chat.open.settings',
                         'ai_chatbot.settings.open.agent_select', 'ai_chatbot.select.back', 'ai_chatbot.agent.select'} <= events)
        for asset in document['assets']:
            if isinstance(asset, dict):
                for _, node in walk(asset.get('node', asset)):
                    if node.get('type') == 'label':
                        self.assertGreaterEqual(int(node['style']['fontSize'].removesuffix('sp')), 16)
        for screen in [asset for asset in document['assets'] if isinstance(asset, dict) and asset['type'] == 'viewScreen']:
            for node in screen.get('children', []):
                self.assert_in_circle(node['placement'])
        self.assertLess(metrics['peak'], 800_000)

    def assert_in_circle(self, placement):
        x, y, width, height = [float(placement[key].removesuffix('dp')) for key in ('x', 'y', 'width', 'height')]
        for corner_x in (x, x + width):
            for corner_y in (y, y + height):
                self.assertLessEqual((corner_x - 233)**2 + (corner_y - 233)**2, 233**2)

    def test_calculator_all_keys_remain_reachable_with_readable_labels(self):
        document = json.loads((RESOURCES / 'calculator_round.json').read_text())
        screen = next(asset for asset in document['assets'] if isinstance(asset, dict) and asset['type'] == 'viewScreen')
        display, keypad = screen['children'][0]['children']
        self.assert_in_circle(display['placement'])
        self.assertEqual(len(keypad['children']), 19)
        actions = set()
        for button in keypad['children']:
            self.assert_in_circle(button['placement'])
            self.assertGreaterEqual(float(button['placement']['height'].removesuffix('dp')), 44)
            self.assertEqual(button['children'][0]['style']['fontSize'], '24sp')
            actions.add(button['events'][0]['action'])
        self.assertEqual(len(actions), 19)
        for action in ['calculator.key.clear', 'calculator.key.backspace', 'calculator.key.equals',
                       'calculator.key.add', 'calculator.key.multiply', 'calculator.key.divide']:
            self.assertIn(action, actions)


if __name__ == '__main__':
    unittest.main()
