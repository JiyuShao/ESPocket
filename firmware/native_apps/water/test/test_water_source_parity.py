"""Compare production particle integration to the pinned original, not a rewritten oracle."""
from pathlib import Path
import re
import unittest
from test_water import ROOT, run


class WaterSourceParityTest(unittest.TestCase):
    def test_locked_particle_solver_parity(self):
        source=(ROOT.parent/'badge/upstream/main/apps/app_water.c').read_text()
        source=re.sub(r'/\*.*?\*/', '', source, flags=re.S)
        source=re.sub(r'//[^\n]*', '', source)

        def function(name):
            match=re.search(r'static (?:inline )?[^\n]+\b'+name+r'\([^;]*?\)\s*\{', source)
            begin=source.index('{', match.start())
            depth=1
            end=begin+1
            while depth:
                depth += (source[end]=='{') - (source[end]=='}')
                end += 1
            return source[match.start():end]

        layout=source[source.index('    int n = 0;', source.index('lv_timer_t *water_start')):source.index('    s_field =', source.index('lv_timer_t *water_start'))]
        solver='\n'.join(function(name) for name in ('grid_build_from_current','frsqrt','clamp_circle','neighbors_relax','fluid_step'))
        run(r'''
#include <cassert>
#include <bit>
#include <cmath>
#include <cstring>
#include "espocket/water_simulation.hpp"
namespace original {
constexpr int CX=233,CY=233,R=222,NP=380,GC=24,NB_MAX=128;
constexpr float HR=22,HR2=HR*HR,INV_HR=1/HR,INV_GS=GC/466.0f,KSTIFF=26000,KNEAR=78000;
float s_x[NP],s_y[NP],s_px[NP],s_py[NP],s_vx[NP],s_vy[NP],s_rho0;
uint16_t s_head[GC*GC],s_next[NP];
#define ESP_LOGW(...) ((void)0)
''' + solver + '\nvoid initialize(){\n' + layout + r'''
}
uint64_t fingerprint(){uint64_t h=14695981039346656037ULL;
 for(int i=0;i<NP;++i)for(float v:{s_x[i],s_y[i],s_vx[i],s_vy[i]}){h^=std::bit_cast<uint32_t>(v);h*=1099511628211ULL;}return h;}
}
int main(){using namespace espocket::water;Simulation production;assert(production.initialize());original::initialize();
 assert(production.diagnostics().fingerprint==original::fingerprint());auto frame=Frame::create();std::atomic_bool cancelled{false};
 for(int i=0;i<40;++i){
  const float dt=33u*0.001f,sub_dt=dt/4;
  for(int k=0;k<4;++k)original::fluid_step(sub_dt,0,1900);
  assert(production.advance(33,{},*frame,cancelled));
  assert(production.diagnostics().fingerprint==original::fingerprint());
 }
}
''')

if __name__=='__main__': unittest.main()
