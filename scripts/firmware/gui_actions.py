"""Read-only comparison of GUI events and C++ action subscriptions/handlers."""

from collections import defaultdict
import json
from pathlib import Path
import re


def action_sets(component: Path, source_name: str, class_name: str):
    document = json.loads((component / 'resources/gui.json').read_text())
    owners = defaultdict(list)

    def visit(node):
        if isinstance(node, dict):
            for event in node.get('events', []):
                if action := event.get('action'):
                    owners[action].append(node.get('id', '<unknown>'))
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(document)
    source = (component / 'src' / source_name).read_text()
    constants = dict(re.findall(r'constexpr std::string_view (\w+) = "([^"]+)";', source))

    def method(name):
        match = re.search(rf'{class_name}::{name}\(.*?\n\}}', source, re.DOTALL)
        if not match:
            raise ValueError(f'{class_name}::{name} not found')
        return match.group(0)

    start = method('on_start')
    subscription_names = re.findall(r'subscribe_action\((\w+)\)', start)
    if 'action' in subscription_names:
        loop = re.search(r'for \(const auto action : \{(.*?)\}\)', start, re.DOTALL)
        if not loop:
            raise ValueError('unrecognized action subscription loop')
        subscription_names.remove('action')
        subscription_names += re.findall(r'\b\w+_ACTION\b', loop.group(1))
    handler_names = re.findall(r'\baction\s*(?:==|!=)\s*(\w+)', method('on_action'))
    subscribed = {constants[name] for name in subscription_names}
    handled = {constants[name] for name in handler_names}
    return dict(owners), subscribed, handled


def validate_action_contract(component: Path, source_name: str, class_name: str):
    owners, subscribed, handled = action_sets(component, source_name, class_name)
    declared = set(owners)
    if declared != subscribed or declared != handled:
        raise ValueError(
            f'GUI action mismatch: declared={sorted(declared)}, '
            f'subscribed={sorted(subscribed)}, handled={sorted(handled)}'
        )
