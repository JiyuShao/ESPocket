import json
import re
import unittest
from collections import defaultdict
from pathlib import Path


SHELL_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src/circular_shell.cpp"
)


class ShellDocumentActionsTest(unittest.TestCase):
    def test_each_action_has_one_document_owner(self):
        source = SHELL_SOURCE.read_text()
        match = re.search(
            r'constexpr std::string_view SHELL_JSON = R"json\((.*?)\)json";',
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        document = json.loads(match.group(1))
        owners = defaultdict(list)

        def visit(node):
            if isinstance(node, dict):
                for event in node.get("events", []):
                    action = event.get("action")
                    if action:
                        owners[action].append(node.get("id", "<unknown>"))
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)

        visit(document)
        duplicates = {
            action: nodes for action, nodes in owners.items() if len(nodes) > 1
        }
        self.assertEqual(duplicates, {})


if __name__ == "__main__":
    unittest.main()
