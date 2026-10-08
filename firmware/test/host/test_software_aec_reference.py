"""Bounded software AEC reference preserves near-end audio and rejects stale PCM."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class SoftwareAecReferenceTest(unittest.TestCase):
    def test_alignment_delay_expiry_failure_reset_and_capture(self):
        with tempfile.TemporaryDirectory(prefix='software-aec-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_hal_adaptor',
                                ROOT / 'firmware/patches/espressif__brookesia_hal_adaptor/0.8.4/manifest.json',
                                temporary / 'component')
            code = r'''
#include <cassert>
#include <array>
#include "software_aec_reference.hpp"
using esp_brookesia::hal::SoftwareAecReference;
int main(){
 SoftwareAecReference reference;
 assert(!reference.configure(true,48000,2,16,0));
 assert(!reference.configure(true,16000,1,16,0));
 assert(!reference.configure(true,16000,2,32,0));
 assert(!reference.configure(true,16000,2,16,251));
 assert(reference.configure(true,16000,2,16,10));
 std::array<int16_t,640> output, capture;
 for(int i=0;i<320;i++){output[i*2]=i+100;output[i*2+1]=999;capture[i*2]=42;capture[i*2+1]=777;}
 reference.record_output((uint8_t*)output.data(),sizeof(output),1000000);
 assert(reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),1030000));
 for(int i=0;i<320;i++){assert(capture[i*2]==42);assert(capture[i*2+1]==i+100);}
 reference.invalidate();reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),1030000);
 for(int i=0;i<320;i++)assert(capture[i*2+1]==0);
 reference.record_output((uint8_t*)output.data(),sizeof(output),1000000);
 reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),2030000);
 for(int i=0;i<320;i++)assert(capture[i*2+1]==0);
 // Ring wrap cannot make newer audio appear as old capture reference.
 reference.record_output((uint8_t*)output.data(),sizeof(output),1500000);
 reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),1030000);
 for(int i=0;i<320;i++)assert(capture[i*2+1]==0);
 assert(!reference.inject_reference((uint8_t*)capture.data(),3,1030000));
 assert(reference.configure(true,16000,2,16,0));
 reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),1520000);
 for(int i=0;i<320;i++)assert(capture[i*2+1]==0);
 assert(reference.configure(false,16000,2,16,10));capture.fill(77);
 reference.inject_reference((uint8_t*)capture.data(),sizeof(capture),1030000);
 for(auto value:capture)assert(value==77);
}
'''
            source = temporary / 'test.cpp'
            source.write_text(code)
            binary = temporary / 'test'
            subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-pthread',
                            '-I', str(component / 'src/audio'), str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
