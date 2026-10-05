"""Run the real Shell status refresh without blocking foreground App callbacks."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
OWNER = Path(__file__).resolve().parents[1]


class StatusRefreshDeferralTest(unittest.TestCase):
    def test_foreground_defers_status_reads_and_return_refreshes_once(self):
        text = (OWNER / 'src/shell_status.cpp').read_text()
        begin = text.index('void CircularShell::refresh_status()')
        method = text[begin:text.index('void CircularShell::refresh_developer_mode()', begin)]
        code = r'''
#include <cassert>
#include <functional>
namespace espocket {
struct CircularShell {
 struct Host {std::function<bool()> app_visible;} host_;
 bool status_refresh_deferred_=false;
 unsigned calls=0;
 void refresh_status();
 void refresh_clock(){++calls;}void refresh_wifi(){++calls;}
 void refresh_battery(){++calls;}void refresh_brightness(){++calls;}
 void refresh_developer_mode(){++calls;}
};
''' + method + r'''
}
int main() {
 espocket::CircularShell shell;bool visible=true;
 shell.host_.app_visible=[&]{return visible;};
 for(int i=0;i<200;++i)shell.refresh_status();
 assert(shell.calls==0 && shell.status_refresh_deferred_);
 visible=false;shell.refresh_status();
 assert(shell.calls==5 && !shell.status_refresh_deferred_);
 // Absence of a foreground provider preserves the standalone Shell behavior.
 shell.host_.app_visible={};shell.refresh_status();assert(shell.calls==10);
}
'''
        with tempfile.TemporaryDirectory() as directory:
            cpp=Path(directory)/'status.cpp';binary=Path(directory)/'status';cpp.write_text(code)
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23',str(cpp),'-o',str(binary)],check=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

if __name__ == '__main__': unittest.main()
