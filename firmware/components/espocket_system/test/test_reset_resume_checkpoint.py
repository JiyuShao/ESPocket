from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class ResetResumeCheckpointTest(unittest.TestCase):
    def test_reset_consumes_once_home_clears_and_storage_fails_closed(self):
        code = r'''
#include <cassert>
#include "espocket/reset_resume_checkpoint.hpp"
int main(){
 std::string stored;bool fail=false;int writes=0;
 auto load=[&]()->std::expected<std::string,std::string>{return stored;};
 auto save=[&](std::string_view id)->std::expected<void,std::string>{
  if(fail)return std::unexpected("storage_failed");stored=id;++writes;return {};};
 espocket::ResetResumeCheckpoint c(load,save);
 assert(c.remember("chat") && stored=="chat");assert(c.remember("chat") && writes==1);
 auto target=c.consume(true);assert(target && *target=="chat" && stored.empty());
 assert(c.consume(true)->empty());
 assert(c.remember("chat"));assert(c.remember(""));assert(c.consume(true)->empty());
 assert(c.remember("chat"));assert(c.consume(false)->empty() && stored.empty());
 assert(c.remember("chat"));fail=true;assert(!c.consume(true) && stored=="chat");
 fail=false;assert(c.consume(true)=="chat");
 fail=true;assert(!c.remember("next") && stored.empty());
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-reset-checkpoint-') as temporary:
            directory=Path(temporary);path=directory/'test.cpp';path.write_text(code)
            binary=directory/'test'
            subprocess.run([os.environ.get('CXX','clang++'),'-std=c++23','-I',str(COMPONENT/'include'),str(path),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)


if __name__=='__main__': unittest.main()
