"""GUI event declarations must match subscriptions and handlers."""

from pathlib import Path
import sys
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from gui_actions import action_sets, validate_action_contract


class DocumentActionsTest(unittest.TestCase):
    def test_each_action_has_one_document_owner(self):
        owners, _, _ = action_sets(COMPONENT, 'hello_app.cpp', 'HelloApp')
        self.assertEqual({action: nodes for action, nodes in owners.items()
                          if len(nodes) > 1}, {})

    def test_document_subscriptions_and_handlers_agree(self):
        validate_action_contract(COMPONENT, 'hello_app.cpp', 'HelloApp')


if __name__ == '__main__':
    unittest.main()
