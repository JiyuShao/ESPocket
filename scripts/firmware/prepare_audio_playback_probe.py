#!/usr/bin/env python3
"""Add an explicit AudioPlayback probe to an already staged, isolated audio candidate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import wave

ROOT = Path(__file__).resolve().parents[2]


def prepare(project):
    project = project.resolve()
    if project == ROOT or ROOT in project.parents or project in ROOT.parents:
        raise ValueError('Probe project must be outside the checkout')
    config = (project / 'sdkconfig').read_text()
    from build_patched_firmware import verify_audio_config
    verify_audio_config(config)
    if 'CONFIG_ESP_AUDIO_SIMPLE_PLAYER_FILE_EN=y' not in config:
        raise ValueError('Official player file input is disabled')
    component = project / 'components/espocket_system'
    adapter = component / 'src/settings_navigation_adapter.cpp'
    if adapter.read_bytes() != (ROOT / 'firmware/components/espocket_system/src/settings_navigation_adapter.cpp').read_bytes():
        raise ValueError('Adapter must match the uninstrumented checkout')
    cmake = component / 'CMakeLists.txt'
    if cmake.read_bytes() != (ROOT / 'firmware/components/espocket_system/CMakeLists.txt').read_bytes():
        raise ValueError('Component CMake must match the checkout')
    fixture = component / 'audio_playback_probe.hpp'
    shutil.copyfile(ROOT / 'firmware/test/device/fixtures/audio_playback_probe.hpp', fixture)
    wav = component / 'espocket_audio_probe.wav'
    # 0.5 s quiet sine, then 0.5 s silence. No network or copyrighted recording.
    with wave.open(str(wav), 'wb') as output:
        output.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        output.writeframes(b''.join(struct.pack('<h', round(4096 * math.sin(2 * math.pi * 400 * i / 16000)) if i < 8000 else 0) for i in range(16000)))
    text = adapter.read_text().replace('#include <array>', '#include "../audio_playback_probe.hpp"\n\n#include <array>', 1)
    needle = '    auto result = app_->on_action(context, action);\n    refresh_availability();'
    if text.count(needle) != 1:
        raise ValueError('Unexpected action seam')
    text = text.replace(needle, '    auto result = app_->on_action(context, action);\n    if (result && action == "settings.open.sound") {\n        if (auto probe = audio_probe::start(); !probe)\n            ESP_LOGE("AUDIO-PROBE", "Start failed: %s", probe.error().c_str());\n    }\n    refresh_availability();')
    text = text.replace('    return app_->on_stop(context);', '    auto probe = audio_probe::stop();\n    auto result = app_->on_stop(context);\n    return !probe ? probe : result;', 1)
    text = text.replace('    auto result = app_->on_action(*context_, BACK_ACTION);', '    if (auto probe = audio_probe::stop(); !probe) return probe;\n    auto result = app_->on_action(*context_, BACK_ACTION);', 1)
    adapter.write_text(text)
    cmake.write_text(cmake.read_text().replace('    EMBED_TXTFILES', '    EMBED_FILES "espocket_audio_probe.wav"\n    EMBED_TXTFILES', 1))
    (project.parent / 'audio-probe-inputs.json').write_text(json.dumps({
        'purpose': 'temporary playback/volume hearing gate; never production',
        'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'wav_sha256': hashlib.sha256(wav.read_bytes()).hexdigest(),
        'loop_count': 30, 'configured_timeout_ms': 35000,
        'trigger': 'Settings Sound action', 'cleanup': 'official Stop and Storage FSRemove on Back/Home; checked absence before serialized fixture creation',
        'recorder': False, 'volume_and_mute_changed_by_probe': False,
    }, indent=2) + '\n')
    return project


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(prepare(args.project))
    except (ValueError, OSError) as error:
        parser.exit(1, f'Audio probe rejected: {error}\n')
