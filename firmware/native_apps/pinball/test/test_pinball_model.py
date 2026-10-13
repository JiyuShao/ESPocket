"""Execute production pinball physics and input state."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

def run(code):
    with tempfile.TemporaryDirectory(prefix='pinball-test-') as d:
        cpp, binary = Path(d) / 'test.cpp', Path(d) / 'test'
        cpp.write_text(code)
        subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra', '-I', str(ROOT / 'include'), str(cpp), str(ROOT / 'src/pinball_model.cpp'), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)

class PinballModelTest(unittest.TestCase):
    def test_board_collisions_scores_targets_drain_and_game_over(self):
        run(r'''
#include <cassert>
#include <algorithm>
#include <cmath>
#include "espocket/pinball_model.hpp"
using namespace espocket::pinball;
State& state(Model&m){return const_cast<State&>(m.state());}
void release(Model&m,int&seq){m.advance(0,true,false,++seq,{});}
void physics(Model&m,int&seq){m.advance(20,true,false,++seq,{});}
void start(Model&m,int&seq){release(m,seq);m.advance(0,true,false,++seq,{{233,390,1}});release(m,seq);}

int main(){
 Model m;auto&s=state(m);assert(s.phase==Phase::Ready&&s.points==0&&s.balls==3);
 assert(s.bumper_x[0]==233&&s.bumper_y[0]==105&&s.target_x[0]==83&&s.target_y[0]==155);
 int seq=0;start(m,seq);assert(s.phase==Phase::Playing);
 // A bumper hit adds ten points and sends the ball away from the centre.
 s.x=s.bumper_x[0];s.y=s.bumper_y[0]+27;s.vx=0;s.vy=-3;auto tones=m.advance(20,true,false,++seq,{});
 assert(!tones.empty()&&tones.front().hz==1100&&s.points==10&&s.vy>0);
 // A standing target is worth 50; the fourth target gives the 200 point reset bonus.
 s.target_up.fill(true);s.x=s.target_x[0];s.y=s.target_y[0]-16;s.vx=0;s.vy=3;tones=m.advance(20,true,false,++seq,{});
 assert(s.points==60&&!s.target_up[0]&&tones.front().hz==1400);
 for(int i=0;i<target_count;++i)s.target_up[i]=true;s.points=0;s.x=s.target_x[0];s.y=s.target_y[0]-16;s.vx=0;s.vy=3;
 for(int i=0;i<target_count;++i){s.x=s.target_x[i];s.y=s.target_y[i]-16;s.vx=0;s.vy=3;tones=m.advance(20,true,false,++seq,{});}
 // The model resets all targets after the last target and awards the bonus.
 assert(s.points==400&&std::all_of(s.target_up.begin(),s.target_up.end(),[](bool v){return v;}));
 // A flipper touch is stateful, and a drain consumes one ball while preserving score.
 m.reset();s=state(m);start(m,seq);m.advance(0,true,false,++seq,{{100,400,2},{360,400,3}});assert(s.flippers[0].on&&s.flippers[1].on);
 m.advance(0,true,false,++seq,{});assert(!s.flippers[0].on&&!s.flippers[1].on);
 s.x=233;s.y=440;s.vx=0;s.vy=5;physics(m,seq);assert(s.balls==2&&s.phase==Phase::Playing&&s.points==0);
 for(int i=0;i<2;++i){s.x=233;s.y=440;s.vx=0;s.vy=5;physics(m,seq);}assert(s.balls==0&&s.phase==Phase::GameOver);
 // Game over starts a fresh run only after a release and a new tap.
 release(m,seq);m.advance(0,true,false,++seq,{{233,390,8}});assert(s.phase==Phase::Playing&&s.balls==3&&s.points==0);
 // Pause clears the partial timer and touch state; duplicate frames do nothing.
 m.suspend();assert(!s.flippers[0].on&&!s.flippers[1].on);const float x=s.x; m.advance(19,true,false,++seq,{});m.advance(0,true,false,seq,{});assert(s.x==x);
 Model other;assert(other.state().points==0&&other.state().balls==3);
}
''')

    def test_fixed_step_bound_and_input_cancel(self):
        run(r'''
#include <cassert>
#include <algorithm>
#include "espocket/pinball_model.hpp"
using namespace espocket::pinball;
int main(){Model m;auto&s=const_cast<State&>(m.state());int seq=0;
 m.advance(0,true,false,++seq,{});m.advance(0,true,false,++seq,{{233,390,1}});m.advance(0,true,false,++seq,{});assert(s.phase==Phase::Playing);
 s.x=233;s.y=233;s.vx=1;s.vy=0;m.advance(19,true,false,++seq,{});assert(s.x==233);m.advance(1,true,false,++seq,{});assert(s.x!=233);
 const float after=s.x;m.advance(2000,true,false,++seq,{});assert(s.x>after); // at most five physical steps
 m.advance(0,false,true,++seq,{{100,400,1}});assert(!s.flippers[0].on&&!s.flippers[1].on);
 m.advance(0,true,false,++seq,{{100,400,1}});assert(!s.flippers[0].on);m.advance(0,true,false,++seq,{});m.advance(0,true,false,++seq,{{100,400,1}});assert(s.flippers[0].on);
}
''')

if __name__ == '__main__': unittest.main()
