import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMU = ROOT.parents[1] / "components" / "espocket_imu"


def run(code):
    with tempfile.TemporaryDirectory(prefix="gravity-maze-test-") as directory:
        d = Path(directory)
        source = d / "test.cpp"
        binary = d / "test"
        source.write_text(code)
        subprocess.run([
            os.environ.get("CXX", "clang++"), "-std=c++23", "-Wall", "-Wextra", "-Werror",
            "-I", str(ROOT / "include"), "-I", str(IMU / "include"), str(source),
            str(ROOT / "src" / "gravity_maze_model.cpp"), str(IMU / "src" / "imu_source.cpp"),
            "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


class GravityMazeModelTest(unittest.TestCase):
    def test_touch_fallback_bounces_and_scores(self):
        run(r'''
#include <cassert>
#include <cmath>
#include "espocket/gravity_maze_model.hpp"
using namespace espocket::gravity_maze;
int main() {
    Model model; int sequence = 0;
    model.advance(0, true, false, ++sequence, {}); // release gate
    model.advance(25, true, false, ++sequence, {{400, 233, 1}});
    assert(std::fabs(model.state().velocity_y) > 0.01f);
    auto &state = const_cast<State &>(model.state());
    state.marble_x = state.hole_x; state.marble_y = state.hole_y;
    model.advance(25, true, false, ++sequence, {});
    assert(state.score == 1);
    state.marble_x = 233; state.marble_y = 434; state.velocity_x = 0; state.velocity_y = 4;
    model.advance(25, true, false, ++sequence, {});
    assert(state.marble_y < 434 && state.velocity_y < 0);
}
''')

    def test_sample_units_reference_and_sequence_cancellation(self):
        run(r'''
#include <cassert>
#include "espocket/gravity_maze_model.hpp"
using namespace espocket::gravity_maze;
using espocket::imu::Sample;
int main() {
    Model model; int sequence = 0; model.advance(0, true, false, ++sequence, {});
    Sample sample{.accel_x_mg=0, .accel_y_mg=0, .accel_z_mg=1000, .accel_valid=true};
    model.advance(25, true, false, ++sequence, {}, sample);
    sample.accel_y_mg = 500;
    model.advance(25, true, false, ++sequence, {}, sample);
    const auto y = model.state().velocity_x;
    model.advance(25, true, false, sequence, {}, sample);
    assert(model.state().velocity_x == y); // duplicate sequence is ignored
    model.advance(0, false, true, ++sequence, {{100,100,1}}, sample);
    assert(model.state().velocity_x == y); // cancellation clears input, not physics state
}
''')


if __name__ == "__main__":
    unittest.main()
