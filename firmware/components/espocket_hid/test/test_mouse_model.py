import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMU = ROOT.parent / "espocket_imu"


def run(code):
    with tempfile.TemporaryDirectory(prefix="mouse-model-test-") as directory:
        d = Path(directory); source = d / "test.cpp"; binary = d / "test"; source.write_text(code)
        subprocess.run([
            os.environ.get("CXX", "clang++"), "-std=c++23", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "include"), "-I", str(IMU / "include"), str(source),
            str(ROOT / "src" / "mouse_endpoint.cpp"), str(ROOT / "src" / "mouse_model.cpp"),
            str(IMU / "src" / "imu_source.cpp"), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


class MouseModelTest(unittest.TestCase):
    def test_report_and_boot_protocol_payloads(self):
        run(r'''
#include <array>
#include <cassert>
#include <climits>
#include "espocket/mouse_endpoint.hpp"
using namespace espocket::hid;
int main() {
  static_assert(sizeof(encode_mouse_report({})) == 4);
  static_assert(sizeof(encode_boot_mouse_report({})) == 3);
  const auto full = encode_mouse_report({255, INT_MAX, INT_MIN, INT_MIN});
  assert((full == std::array<uint8_t, 4>{7, 127, 129, 129}));
  const auto boot = encode_boot_mouse_report({255, INT_MAX, INT_MIN, INT_MAX});
  assert((boot == std::array<uint8_t, 3>{7, 127, 129}));
  const auto boundaries = encode_mouse_report({0, -127, 127, 127});
  assert((boundaries == std::array<uint8_t, 4>{0, 129, 127, 127}));
  assert((encode_mouse_report({}) == std::array<uint8_t, 4>{0, 0, 0, 0}));
  assert((encode_boot_mouse_report({0, 0, 0, 12}) == std::array<uint8_t, 3>{0, 0, 0}));
}
''')

    def test_unavailable_endpoint_fails_closed(self):
        run(r'''
#include <cassert>
#include "espocket/mouse_endpoint.hpp"
int main() { espocket::hid::UnavailableEndpoint endpoint; auto started=endpoint.start(); assert(!started&&started.error()==espocket::hid::Error::unavailable); assert(!endpoint.send({})); }
''')

    def test_trackpad_tap_drag_ring_and_cancel(self):
        run(r'''
#include <cassert>
#include <cmath>
#include "espocket/mouse_model.hpp"
using namespace espocket::hid;
int main() {
  MouseModel m; m.set_connected(true); int seq=0;
  m.advance(15,true,false,++seq,{}); m.advance(15,true,false,++seq,{{233,233,1}});
  auto click=m.advance(15,true,false,++seq,{}); assert(click.size()==2&&click[0].buttons==1&&click[1].buttons==0);
  m.advance(15,true,false,++seq,{{233,180,1}}); auto move=m.advance(15,true,false,++seq,{{260,180,1}}); assert(!move.empty()&&move[0].dx>0);
  m.advance(15,true,false,++seq,{}); m.advance(15,true,false,++seq,{{400,233,1}}); auto wheel=m.advance(15,true,false,++seq,{{400,350,1}}); assert(!wheel.empty()&&wheel[0].wheel!=0);
  m.advance(0,false,true,++seq,{{1,1,1}}); assert(!m.state().button_down);
}
''')

    def test_air_sample_and_disconnect_drop_reports(self):
        run(r'''
#include <cassert>
#include "espocket/mouse_model.hpp"
using namespace espocket::hid; using espocket::imu::Sample;
int main() { MouseModel m; m.set_connected(true); m.toggle_mode(); int seq=0; m.advance(15,true,false,++seq,{});
  Sample s{.accel_x_mg=0,.accel_y_mg=0,.accel_z_mg=1000,.accel_valid=true}; m.advance(15,true,false,++seq,{},s); s.accel_y_mg=1000; auto out=m.advance(50,true,false,++seq,{},s); assert(!out.empty());
  m.set_connected(false); assert(m.advance(50,true,false,++seq,{},s).empty());
}
''')


if __name__ == "__main__": unittest.main()
