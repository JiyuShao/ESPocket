#!/usr/bin/env python3
"""Materialize the locked Settings component needed by host compatibility tests.

Separate from read-only checks. Uses IDF Component Manager 3.0.3, as in IDF 6.0.1.
"""

from pathlib import Path

from idf_component_tools.hash_tools.validate import validate_hash_eq_hashdir
from idf_component_tools.lock.manager import LockManager
from idf_component_tools.sources.fetcher import ComponentFetcher

ROOT = Path(__file__).resolve().parents[2]


def main():
    solution = LockManager(ROOT / 'firmware/dependencies.lock').load()
    component = next(item for item in solution.dependencies
                     if item.name == 'espressif/brookesia_app_settings')
    destination = ROOT / 'firmware/managed_components'
    existing = destination / 'espressif__brookesia_app_settings'
    if existing.exists():
        validate_hash_eq_hashdir(str(existing), component.component_hash)
    else:
        destination.mkdir(parents=True, exist_ok=True)
        if not ComponentFetcher(component, destination).download():
            raise RuntimeError('Settings dependency was not materialized')
        validate_hash_eq_hashdir(str(existing), component.component_hash)
    print(f'Host dependency ready: {component.name} {component.version}')


if __name__ == '__main__':
    main()
