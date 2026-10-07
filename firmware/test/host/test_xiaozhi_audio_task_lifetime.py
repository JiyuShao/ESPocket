import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class XiaoZhiAudioTaskLifetimeTest(unittest.TestCase):
    def exercise(self, component, directory, static):
        source = (component / 'src/esp_xiaozhi_chat.c').read_text()
        exit_method = source[source.index('static void esp_xiaozhi_chat_audio_input_exit('):
                             source.index('static esp_err_t esp_xiaozhi_chat_create_audio_input_task(')]
        start = source.index('static void esp_xiaozhi_chat_audio_input(void *pvParameter)\n{')
        invalid_input = source[start:source.index('    evt = xiaozhi_chat->udp->audio_receive_events;', start)] + '}\n'
        code = r'''
#include <stddef.h>
#include <stdio.h>
#define ESP_LOGE(...)
#define ESP_XIAOZHI_CHAT_RECV_TASK_EXITED 1
typedef int *EventGroupHandle_t;
typedef struct { EventGroupHandle_t audio_receive_events; } Udp;
typedef struct { Udp *udp; } esp_xiaozhi_chat_t;
size_t outstanding_stack_bytes;
void xEventGroupSetBits(EventGroupHandle_t events, int bits) { *events |= bits; }
void vTaskDelete(void *task) { (void)task; }
void vTaskDeleteWithCaps(void *task) { (void)task; outstanding_stack_bytes -= 8192; }
''' + exit_method + invalid_input + r'''
int main(void) {
    for (int cycle = 0; cycle < 32; ++cycle) {
        int events = 0;
        if (!CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_STATIC) outstanding_stack_bytes += 8192;
        esp_xiaozhi_chat_audio_input_exit(&events);
        if (events != ESP_XIAOZHI_CHAT_RECV_TASK_EXITED) return 2;
    }
    if (!CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_STATIC) outstanding_stack_bytes += 8192;
    esp_xiaozhi_chat_audio_input(NULL);
    Udp udp = {NULL};
    esp_xiaozhi_chat_t chat = {&udp};
    if (!CONFIG_XIAOZHI_AUDIO_TASK_ALLOC_STATIC) outstanding_stack_bytes += 8192;
    esp_xiaozhi_chat_audio_input(&chat);
    if (outstanding_stack_bytes) {
        fprintf(stderr, "Unreleased capped task stacks: %zu bytes\n", outstanding_stack_bytes);
        return 1;
    }
    return 0;
}
'''
        harness = directory / 'lifetime.c'
        executable = directory / 'lifetime'
        harness.write_text(code)
        subprocess.run([os.environ.get('CC', 'clang'), '-std=c11',
                        f'-DCONFIG_XIAOZHI_AUDIO_TASK_ALLOC_STATIC={int(static)}',
                        str(harness), '-o', str(executable)], check=True)
        return subprocess.run([str(executable)], text=True, capture_output=True)

    def test_dynamic_audio_task_releases_capped_stacks_on_all_exits(self):
        component = ROOT / 'firmware/managed_components/espressif__esp_xiaozhi'
        with tempfile.TemporaryDirectory(prefix='espocket-xiaozhi-task-') as temporary:
            directory = Path(temporary)
            original = self.exercise(component, directory, False)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('Unreleased capped task stacks', original.stderr)
            patched = prepare(component, ROOT / 'firmware/patches/espressif__esp_xiaozhi/0.1.2/manifest.json',
                              directory / 'patched')
            for static in (False, True):
                with self.subTest(static=static):
                    fixed = self.exercise(patched, directory, static)
                    self.assertEqual(fixed.returncode, 0, fixed.stderr)
