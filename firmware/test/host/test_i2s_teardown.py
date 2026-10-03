"""Run Board Manager's actual teardown after a codec has stopped its channel."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
COMPONENT = 'espressif__esp_board_manager'


def run_teardown(source):
    text = (Path(source) / 'peripherals/periph_i2s/periph_i2s.c').read_text()
    text = text[text.index('static int periph_i2s_release_channel(') if 'static int periph_i2s_release_channel(' in text else text.index('int periph_i2s_deinit('):]
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define SOC_I2S_NUM 1
#define ESP_OK 0
#define ESP_IDF_VERSION_VAL(a,b,c) ((a)*10000+(b)*100+(c))
#define ESP_IDF_VERSION 60001
struct channel {bool enabled; bool deleted;};
typedef struct channel *i2s_chan_handle_t;
typedef struct {bool is_enabled;} i2s_chan_info_t;
static struct {i2s_chan_handle_t chan_in,chan_out;bool in_en,out_en;} i2s_chan_handles[1];
static int repeated_disable, info_error, disable_error, delete_error;
int i2s_channel_get_info(i2s_chan_handle_t c,i2s_chan_info_t *info){if(info_error)return -1;info->is_enabled=c->enabled;return 0;}
int i2s_channel_disable(i2s_chan_handle_t c){if(disable_error)return -1;if(!c->enabled){repeated_disable++;return -1;}c->enabled=false;return 0;}
int i2s_del_channel(i2s_chan_handle_t c){if(delete_error)return -1;assert(!c->enabled);c->deleted=true;return 0;}
''' + text + r'''
int main(){
 for(int rx=0;rx<2;rx++)for(int already_stopped=1;already_stopped>=0;already_stopped--)for(int peer_running=0;peer_running<2;peer_running++){
  struct channel c={.enabled=!already_stopped},peer={.enabled=peer_running};
  i2s_chan_handles[0].chan_in=rx?&c:&peer;i2s_chan_handles[0].chan_out=rx?&peer:&c;
  i2s_chan_handles[0].in_en=rx;i2s_chan_handles[0].out_en=!rx;
  assert(periph_i2s_deinit(&c)==0);assert(c.deleted&&peer.deleted);
  assert(!i2s_chan_handles[0].chan_in&&!i2s_chan_handles[0].chan_out);
  assert(repeated_disable==0 && "codec close then Board Manager teardown must not disable stopped I2S again");
 }
 for(int fault=0;fault<3;fault++){
  struct channel c={.enabled=true};i2s_chan_handles[0].chan_out=&c;i2s_chan_handles[0].out_en=true;
  info_error=fault==0;disable_error=fault==1;delete_error=fault==2;
  assert(periph_i2s_deinit(&c)!=0);assert(!c.deleted&&i2s_chan_handles[0].chan_out==&c);
  info_error=disable_error=delete_error=0;
  assert(periph_i2s_deinit(&c)==0);assert(c.deleted);
 }
}
'''
    with tempfile.TemporaryDirectory(prefix='espocket-i2s-test-') as directory:
        src = Path(directory) / 'test.c'
        binary = Path(directory) / 'test'
        src.write_text(harness)
        subprocess.run(['clang', '-std=c11', str(src), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, capture_output=True, text=True)


class I2sTeardownTest(unittest.TestCase):
    def test_original_repeats_codec_disable(self):
        with self.assertRaises(subprocess.CalledProcessError) as failure:
            run_teardown(ROOT / 'firmware/managed_components' / COMPONENT)
        self.assertIn('must not disable stopped I2S again', failure.exception.stderr)

    def test_owner_teardown_handles_stopped_running_and_failures(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-i2s-patch-') as directory:
            source = prepare(ROOT / 'firmware/managed_components' / COMPONENT,
                             ROOT / 'firmware/patches' / COMPONENT / '0.5.15/manifest.json',
                             Path(directory) / 'board')
            run_teardown(source)
