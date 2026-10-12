#!/usr/bin/env python3
"""Inject an explicitly selected reliability probe before isolated input freezing.

No standalone mutation command: called only by build_patched_firmware.stage.
No writes to NVS, device access, or new production API.
"""
from pathlib import Path

MODES = ('lifecycle', 'init-after-theme', 'init-after-cards', 'init-after-shell',
         'start-after-shell', 'start-after-power', 'theme-unknown',
         'theme-apply-failure', 'theme-default-failure')


def replace_once(text, anchor, replacement):
    if text.count(anchor) != 1:
        raise ValueError('Reliability fixture source seam drift: ' + anchor)
    return text.replace(anchor, replacement)


def inject(root, firmware, mode):
    root, firmware = Path(root).resolve(), Path(firmware).resolve()
    if mode not in MODES:
        raise ValueError('Unknown reliability fixture')
    if firmware == root or root in firmware.parents or firmware in root.parents:
        raise ValueError('Reliability fixture must use an isolated project')
    source = firmware / 'components/espocket_system/src/system.cpp'
    main = firmware / 'main/app_main.cpp'
    original = root / 'firmware/components/espocket_system/src/system.cpp'
    if source.read_bytes() != original.read_bytes() or main.read_bytes() != (root / 'firmware/main/app_main.cpp').read_bytes():
        raise ValueError('Reliability fixture requires unchanged product source')
    text = source.read_text()
    failure = '\n    return std::unexpected("Reliability fixture: ' + mode + '");'
    anchors = {
        'init-after-theme': '    if (auto theme = init_product_theme(); !theme) return theme;',
        'init-after-cards': '    init_cards();',
        'init-after-shell': '    ESP_LOGI(TAG, "Circular Shell installed");',
        'start-after-shell': '    auto power_result = power_key_monitor_->start();',
        'start-after-power': '    restore_after_hardware_reset();',
    }
    if mode in anchors:
        anchor = anchors[mode]
        # The shell-start boundary is before starting the PWR monitor.
        replacement = failure.lstrip('\n') + '\n' + anchor if mode == 'start-after-shell' else anchor + failure
        text = replace_once(text, anchor, replacement)
    elif mode == 'theme-unknown':
        # Override only the read result; never poison the persistent preference.
        text = replace_once(text, '    const auto saved_theme = get_stored_gui_theme_id();',
                            '    const auto saved_theme = std::optional<std::string>{"fixture-unknown"};')
    elif mode.startswith('theme-'):
        call = 'system_gui().set_theme(theme, false)'
        text = replace_once(text, call, 'std::expected<void, std::string>{std::unexpected("Reliability fixture: theme apply failure")}')
        if mode == 'theme-default-failure':
            text = replace_once(text, 'system_gui().set_theme("dark", false)',
                                'std::expected<void, std::string>{std::unexpected("Reliability fixture: default failure")}')
        # Force a distinct saved selection so the fallback path is exercised.
        text = replace_once(text, '    const auto saved_theme = get_stored_gui_theme_id();',
                            '    const auto saved_theme = std::optional<std::string>{"light"};')
    template = root / 'firmware/test/device/fixtures/reliability/app_main.cpp'
    entry = replace_once(template.read_text(), 'RELIABILITY_MODE', mode)
    # All seam validation happens before either file is changed.
    source.write_text(text)
    main.write_text(entry)
    return {'mode': mode, 'test_only': True, 'persistent_preferences_modified': False,
            'scope': 'selected product boundary; not exhaustive Core/GUI fault injection'}
