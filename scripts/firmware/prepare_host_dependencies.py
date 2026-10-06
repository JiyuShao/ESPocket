#!/usr/bin/env python3
"""Materialize the locked component sources exercised by host checks.

Separate from read-only checks. Uses IDF Component Manager 3.0.3, as in IDF 6.0.1.
"""

from pathlib import Path

from idf_component_tools.hash_tools.validate import validate_hash_eq_hashdir
from idf_component_tools.lock.manager import LockManager
from idf_component_tools.sources.fetcher import ComponentFetcher

ROOT = Path(__file__).resolve().parents[2]


def main():
    solution = LockManager(ROOT / 'firmware/dependencies.lock').load()
    destination = ROOT / 'firmware/managed_components'
    names = (
        'espressif/brookesia_app_settings', 'espressif/esp-boost', 'lvgl/lvgl',
        'espressif/brookesia_app_store', 'espressif/brookesia_system_core',
        'espressif/brookesia_gui_interface', 'espressif/brookesia_gui_lvgl',
        'espressif/brookesia_hal_adaptor', 'espressif/brookesia_lib_utils',
        'espressif/brookesia_service_display', 'espressif/brookesia_service_http',
        'espressif/brookesia_service_storage', 'espressif/esp_board_manager',
        'espressif/esp_lv_decoder',
    )
    for name in names:
        component = next(item for item in solution.dependencies if item.name == name)
        existing = destination / name.replace('/', '__')
        if not existing.exists():
            destination.mkdir(parents=True, exist_ok=True)
            if not ComponentFetcher(component, destination).download():
                raise RuntimeError(f'{name} dependency was not materialized')
        validate_hash_eq_hashdir(str(existing), component.component_hash)
        print(f'Host dependency ready: {component.name} {component.version}')



if __name__ == '__main__':
    main()
