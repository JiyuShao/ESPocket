import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class EmptySpeechModelTest(unittest.TestCase):
    def exercise(self, component, directory):
        source = (component / 'src/model_path.c').read_text()
        loader = source[source.index('srmodel_list_t *srmodel_mmap_init('):
                        source.index('void srmodel_mmap_deinit(')]
        initialize = source[source.index('srmodel_list_t *esp_srmodel_init('):
                            source.index('void esp_srmodel_deinit(')]
        code = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define ESP_PLATFORM 1
#define ESP_IDF_VERSION_VAL(major,minor,patch) ((major)*10000+(minor)*100+(patch))
#define ESP_IDF_VERSION ESP_IDF_VERSION_VAL(6,0,1)
#define ESP_PARTITION_MMAP_DATA 1
#define ESP_PARTITION_TYPE_DATA 1
#define ESP_PARTITION_SUBTYPE_ANY 1
#define ESP_OK 0
#define ESP_LOGI(...)
#define ESP_LOGE(...)
#define ESP_LOGW(...)
#define ESP_ERROR_CHECK(result) do { if ((result) != 0) abort(); } while (0)
#define SRMODEL_STRING_LENGTH 32
typedef int esp_err_t;
typedef uint32_t esp_partition_mmap_handle_t;
typedef struct { uint32_t size; const char *label; } esp_partition_t;
typedef struct { esp_partition_t *partition; void *mmap_handle; int num; } srmodel_list_t;
static srmodel_list_t *static_srmodels;
static int srmodel_init_refcount;
static uint8_t model_header[4];
static esp_partition_t model_partition = {64, "model"};
static int read_result, reads, maps, loads, missing;
srmodel_list_t *srmodel_list_alloc(void) { return calloc(1, sizeof(srmodel_list_t)); }
uint32_t read_int32(char *data) { return (uint8_t)data[0] | (uint32_t)(uint8_t)data[1]<<8 |
    (uint32_t)(uint8_t)data[2]<<16 | (uint32_t)(uint8_t)data[3]<<24; }
int esp_partition_read(const esp_partition_t *partition, size_t offset, void *data, size_t length) {
    ++reads; if (read_result) return read_result;
    if (partition->size < offset+length || length != 4) abort();
    memcpy(data, model_header, 4); return 0;
}
int spi_flash_mmap_get_free_pages(int type) { return 10000; }
int esp_partition_mmap(const esp_partition_t *partition, int offset, uint32_t size, int type,
    const void **root, esp_partition_mmap_handle_t *handle) {
    ++maps; *root=model_header; *handle=1; return 0;
}
srmodel_list_t *srmodel_load(const void *root) {
    ++loads; static_srmodels->num=read_int32((char *)root); return static_srmodels;
}
const esp_partition_t *esp_partition_find_first(int type, int subtype, const char *label) {
    return missing ? NULL : &model_partition;
}
''' + loader + initialize + r'''
int main(void) {
    for (int scenario=0; scenario<7; ++scenario) {
        memset(model_header, 0, sizeof(model_header)); model_partition.size=64;
        read_result=0; missing=0;
        if (scenario==1) memset(model_header, 255, sizeof(model_header));
        if (scenario==2) model_partition.size=3;
        if (scenario==3) read_result=-1;
        if (scenario==4) model_header[0]=2;
        if (scenario==5) missing=1;
        if (scenario==6) memcpy(model_header, "\xe9\x06\x02\x5f", 4);
        for (int cycle=0; cycle<4; ++cycle) {
            if (esp_srmodel_init("model") || static_srmodels || maps || loads || srmodel_init_refcount) {
                fprintf(stderr, "Empty/invalid model partition admitted: scenario %d\n", scenario); return 1;
            }
        }
    }
    missing=0; read_result=0; model_partition.size=64;
    memset(model_header, 0, sizeof(model_header)); model_header[0]=1;
    int before_reads=reads;
    srmodel_list_t *models=esp_srmodel_init("model");
    if (!models || models->num!=1 || loads!=1 || maps!=1 || srmodel_init_refcount!=1) return 2;
    if (esp_srmodel_init("model")!=models || reads!=before_reads+1 || srmodel_init_refcount!=2) return 3;
    free(models->mmap_handle); free(models);
    return 0;
}
'''
        harness = directory / 'model.c'
        executable = directory / 'model'
        harness.write_text(code)
        subprocess.run([os.environ.get('CC', 'clang'), '-std=c11', str(harness), '-o', str(executable)], check=True)
        return subprocess.run([str(executable)], text=True, capture_output=True)

    def test_empty_or_erased_models_fail_closed_without_allocating_or_retaining(self):
        component = ROOT / 'firmware/managed_components/espressif__esp-sr'
        with tempfile.TemporaryDirectory(prefix='espocket-srmodel-') as temporary:
            directory = Path(temporary)
            original = self.exercise(component, directory)
            self.assertNotEqual(original.returncode, 0)
            self.assertIn('Empty/invalid model partition admitted', original.stderr)
            patched = prepare(component, ROOT / 'firmware/patches/espressif__esp-sr/2.4.4/manifest.json',
                              directory / 'patched')
            fixed = self.exercise(patched, directory)
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
