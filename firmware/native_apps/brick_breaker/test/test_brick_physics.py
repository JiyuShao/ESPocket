"""Deterministic scenarios seed state, then execute production model physics/input."""
import unittest
from test_brick_breaker import run


class BrickPhysicsTest(unittest.TestCase):
    def test_five_original_boards_durability_collisions_lives_and_win(self):
        run(r'''
#include <cassert>
#include <cmath>
#include "espocket/brick_model.hpp"
using namespace espocket::brick;
// Seed a deterministic collision in the production model without a public debug API.
State& seed(Model& m){return const_cast<State&>(m.state());}
auto tick(Model&m){return m.advance(20,false,true,0,{});}
void last_brick(Model&m){
 auto&s=seed(m);s.phase=Phase::Playing;s.obstacle_step=0;
 for(auto&b:s.bricks)b.hp=0;s.bricks[0].hp=1;s.remaining=1;
 auto b=s.bricks[0];s.x=(b.x1+b.x2)/2.0f;s.y=b.y1-ball_radius-1;s.vx=0;s.vy=3;
}
int main(){
 Model m;assert(m.state().phase==Phase::Ready && m.state().lives==3);
 const int counts[]={14,20,10,17,20},tough[]={0,4,4,8,9};
 const float halves[]={26,24,22,20,18},speeds[]={5,5.4,5.8,6.4,7},caps[]={6.5,7,7.5,8.2,9},obstacles[]={0,0,1.2,1.8,2.6};
 for(int level=0;level<5;++level){
  const auto&s=m.state();assert(s.level==level && s.brick_count==counts[level] && s.remaining==counts[level]);
  assert(s.paddle_half==halves[level] && s.speed_start==speeds[level] && s.speed_max==caps[level] && s.obstacle_step==obstacles[level]);
  int hp2=0;for(int i=0;i<s.brick_count;++i){auto b=s.bricks[i];hp2+=b.hp==2;
   assert(b.y1>=80 && b.y2-b.y1==26);
   for(auto x:{b.x1,b.x2})for(auto y:{b.y1,b.y2})assert(std::hypot(x-center,y-center)<=202.1);
  }assert(hp2==tough[level]);
  last_brick(m);auto tones=tick(m);assert(!tones.empty() && tones.front().hz==900 && tones.front().ms==40);
  if(level<4)assert(m.state().phase==Phase::Ready && m.state().lives==3);
 }
 assert(m.state().phase==Phase::Won);const float wonx=m.state().x;tick(m);assert(m.state().x==wonx);
 m.advance(0,true,false,1,{});m.advance(0,true,false,2,{{233,390,1}});
 assert(m.state().level==0 && m.state().phase==Phase::Playing);
 // Reach level 2 and hit a tough brick twice; first contact pushes out and keeps geometry.
 m.reset();last_brick(m);tick(m);auto &s=seed(m);auto b=s.bricks[0];
 s.phase=Phase::Playing;s.x=(b.x1+b.x2)/2.0f;s.y=b.y1-ball_radius-1;s.vx=0;s.vy=3;
 auto tones=tick(m);assert(tones.front().hz==600 && tones.front().ms==30 && s.bricks[0].hp==1 && s.remaining==20 && s.vy<0);
 assert(s.y==b.y1-ball_radius);tick(m);assert(s.bricks[0].hp==1 && s.vy<0);
 s.y=b.y1-ball_radius-1;s.vy=3;tones=tick(m);assert(s.bricks[0].hp==0 && s.remaining==19 && tones.front().hz==900);
 // Side wall and centre paddle reflect inward. Paddle speed ramp is capped.
 m.reset();s=seed(m);s.phase=Phase::Playing;s.x=432;s.y=233;s.vx=5;s.vy=0;
 tick(m);assert(s.vx<0 && s.x==429);
 s.x=233;s.y=430;s.vx=0;s.vy=5;s.speed=6.5;
 tones=tick(m);assert(s.vy<0 && s.y==428 && std::fabs(std::hypot(s.vx,s.vy)-6.5)<0.001 && tones.front().hz==500);
 // Missing keeps the current level and rebuilds it; third miss resets the run.
 m.reset();last_brick(m);tick(m);assert(s.level==1);
 for(int life=2;life>=0;--life){
  s.phase=Phase::Playing;s.paddle_angle=232;s.x=233+0.5f*230;s.y=233+0.8660254f*230;s.vx=0;s.vy=1;
  tick(m);assert(s.phase==Phase::Ready && s.remaining==s.brick_count);
  assert(s.lives==(life?life:3) && s.level==(life?1:0));
 }
 // Rotating obstacle reflects and resolves overlap; each model is independent.
 m.reset();last_brick(m);tick(m);last_brick(m);tick(m);assert(s.level==2);
 for(auto&b:s.bricks)b.hp=0;s.remaining=1;
 s.phase=Phase::Playing;s.obstacle_angle=360-s.obstacle_step;s.x=233;s.y=233-124-22;s.vx=0;s.vy=3;
 tones=tick(m);assert(!tones.empty() && tones.back().hz==700 && tones.back().ms==25 && s.vy<0 && std::fabs(s.y-(233-124-21))<0.01);
 Model other;assert(other.state().level==0 && other.state().lives==3);
}
''')

    def test_fixed_step_input_sequence_track_cancel_and_pause(self):
        run(r'''
#include <cassert>
#include "espocket/brick_model.hpp"
using namespace espocket::brick;
int main(){
 Model m;
 // Initial mount and every cancellation require a full release, even with a new track.
 m.advance(0,true,false,1,{{233,390,1}});assert(m.state().phase==Phase::Ready);
 m.advance(0,true,false,2,{});m.advance(200,true,false,3,{{233,390,1}});
 assert(m.state().phase==Phase::Playing && m.state().x==233); // start tap consumed
 m.advance(0,true,false,4,{{390,233,1}});assert(m.state().paddle_angle==180);
 m.advance(0,true,false,5,{});m.advance(0,true,false,6,{{233,390,8},{50,233,9}});
 m.advance(0,true,false,6,{{390,233,8}});assert(m.state().paddle_angle==180); // repeat
 m.advance(0,true,false,7,{{390,233,8},{50,233,9}});assert(m.state().paddle_angle==128);
 m.advance(0,true,false,8,{{50,233,9}});m.advance(0,true,false,9,{{390,233,9}});assert(m.state().paddle_angle==128); // no finger takeover
 m.advance(0,true,false,10,{});m.advance(0,true,false,11,{{233,390,10}});
 m.advance(0,false,true,12,{});m.advance(0,true,false,13,{{50,233,11}});assert(m.state().paddle_angle==128);
 m.advance(0,true,false,14,{});m.advance(0,true,false,15,{{233,390,11}});
 m.advance(0,true,false,16,{{50,233,11}});assert(m.state().paddle_angle==232);
 // Time advances independently of input snapshots. Whole steps preserve late-frame collision speed.
 auto&s=const_cast<State&>(m.state());s.x=233;s.y=233;s.vx=1;s.vy=0;
 m.advance(19,true,false,17,{});assert(s.x==233);
 m.advance(1,true,false,17,{});assert(s.x==234);
 m.advance(2000,true,false,17,{});assert(s.x==239); // cap five steps
 m.advance(0,true,false,17,{});assert(s.x==244); // bounded accrued remainder
 m.advance(19,true,false,17,{});m.suspend();
 m.advance(1,true,false,18,{});assert(s.x==244); // pause clears partial interval
 m.advance(19,true,false,18,{});assert(s.x==245);
 m.reset();assert(s.x==233 && s.level==0 && s.lives==3 && s.phase==Phase::Ready);
}
''')


if __name__ == '__main__':
    unittest.main()
