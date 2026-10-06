"""Exercise the real Launcher Owner against public GUI failures and stale views."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

OWNER = Path(__file__).resolve().parents[1]


class LauncherReconciliation(unittest.TestCase):
    def test_replacement_failures_and_owner_dispatch(self):
        with tempfile.TemporaryDirectory(prefix='espocket-launcher-owner-') as temporary:
            directory = Path(temporary)
            (directory / 'shell_internal.hpp').write_text((OWNER / 'test/test_launcher_reconciliation.cpp').read_text())
            (directory / 'shell_launcher.cpp').write_text((OWNER / 'src/shell_launcher.cpp').read_text())
            main = r'''
#include "shell_launcher.cpp"
#include <iostream>
using namespace espocket;
void check(bool pass, const char *message) { if (!pass) throw std::runtime_error(message); }
int main() {
 FakeContext context; CircularShell shell; shell.context_ = &context;
 std::vector<LauncherApp> apps{{1,"org.a","A","icon-a",true,true,true,false}};
 uint64_t generation=1; bool fail_snapshot=false;
 shell.host_.launcher_apps=[&](auto)->std::expected<std::vector<LauncherApp>,std::string>{
   if(fail_snapshot)return std::unexpected("snapshot failed");return apps;};
 shell.host_.launcher_generation=[&]{return generation;};
 shell.host_.developer_mode.enabled=[]{return true;};
 bool active=true;shell.host_.app_visible=[&]{return active;};
 for(int i=0;i<200;++i){test_clock_us+=50'000;shell.refresh_launcher();}
 check(context.view.language_reads==0 && context.view.preparations==0,"hidden Launcher acquired GUI during foreground App");
 active=false;
 shell.refresh_launcher();
 check(shell.launcher_entries_.size()==1 && context.view.regions.size()==1,"initial full projection");
 const auto first=shell.launcher_region_; const auto stable=shell.launcher_entries_[0].instance;
 check(context.view.regions.at(first),"first page exposed dynamic rows");
 check(shell.show_launcher_page(1).has_value(),"cannot open runtime page");
 check(!context.view.regions.at(first) && context.view.bindings.at("/launcher/settings:hidden")=="true","runtime page retained fixed rows");
 context.view.fail="swap";
 check(!shell.show_launcher_page(0) && shell.launcher_page_==1,"failed page switch changed committed page");
 context.view.fail.clear();
 for(const auto *failure:{"launcher_region","launcher_item","text","bindings","swap","snapshot"}) {
   context.view.fail=failure;fail_snapshot=std::string(failure)=="snapshot";
   apps[0].name=failure;++generation;++test_clock_us;
   shell.refresh_launcher();
   check(shell.launcher_region_==first && shell.launcher_entries_[0].name=="A","failure changed committed view");
   check(context.view.regions.size()==1 && !context.view.regions.at(first) && context.view.fixed_available,"failure damaged complete/fixed view");
   check(context.view.image_leases["icon-a"]==1,"failure leaked image lease");
   const auto calls=context.view.preparations;
   for(int i=0;i<100;++i){test_clock_us+=50'000;shell.refresh_launcher();}
   check(context.view.preparations<=calls+2,"same failed generation retried without rate limit");
 }
 context.view.fail.clear();fail_snapshot=false;apps[0].name="Updated";apps[0].runtime_id=77;
 ++generation;++test_clock_us;shell.refresh_launcher();
 check(shell.launcher_region_!=first && shell.launcher_entries_[0].instance==stable,"replacement changed manifest instance");
 check(context.view.regions.size()==1 && context.view.image_leases["icon-a"]==1,"replacement duplicated view/image lease");
 shell.launcher_intent_=first+"/"+stable;shell.dispatch_launcher();check(shell.opened.empty(),"retired view click launched");
 shell.launcher_intent_=shell.launcher_region_+"/"+stable;shell.dispatch_launcher();
 check(shell.opened.size()==1 && shell.launcher_intent_.empty(),"valid click was not consumed once");
 shell.dispatch_launcher();check(shell.opened.size()==1,"duplicate launch");
 shell.launcher_intent_=shell.launcher_region_+"/"+stable;apps.clear();shell.dispatch_launcher();
 check(shell.opened.size()==1,"uninstall race launched removed App");
 apps={{2,"org.b","B","missing",true,true,true,false}};context.view.unavailable_icons.insert("missing");
 ++generation;++test_clock_us;shell.refresh_launcher();
 check(shell.launcher_entries_.size()==1 && shell.launcher_images_.empty(),"missing icon prevented text row");
 shell.stop_launcher();check(context.view.regions.empty() && context.view.image_leases["icon-a"]==0,"stop leaked projection resources");
 // on_start resets the first-reconciliation gate after ordinary stop cleanup.
 shell.launcher_generation_=UINT64_MAX;shell.launcher_refresh_at_us_=0;
 shell.refresh_launcher();check(shell.launcher_entries_.size()==1,"Shell restart did not rebuild from Core");
 apps.clear();
 for(int index=0;index<9;++index)apps.push_back({uint32_t(index+1),"org.page."+std::to_string(index),"Page", "",true,true,true,false});
 ++generation;++test_clock_us;shell.refresh_launcher();
 for(size_t requested:{size_t(0),size_t(1),size_t(2),size_t(3),size_t(99)}) {
   check(shell.show_launcher_page(requested).has_value(),"page switch failed");
   const auto page=launcher_page(apps.size(),requested);
   check(shell.launcher_page_==page.index,"page clamp incorrect");
   for(size_t index=0;index<shell.launcher_entries_.size();++index) {
     const auto visible=index+4>=page.begin && index+4<page.end;
     check(context.view.bindings.at(shell.launcher_region_+"/"+shell.launcher_entries_[index].instance+":hidden")== (visible?"false":"true"),"page row visibility incorrect");
   }
 }
 shell.launcher_intent_=shell.launcher_region_+"/"+shell.launcher_entries_[0].instance;
 const auto opened=shell.opened.size();shell.dispatch_launcher();check(shell.opened.size()==opened,"hidden row intent launched");
 apps.clear();++generation;++test_clock_us;shell.refresh_launcher();
 check(shell.launcher_page_==0 && context.view.bindings.at("/launcher/settings:hidden")=="false","removed apps left invalid page");
 shell.stop_launcher();std::cout<<"PASS: real Launcher failure retention, pagination, icon leases, stale view and uninstall races\n";
}'''
            (directory / 'main.cpp').write_text(main)
            executable = directory / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-I', str(OWNER / 'include'),
                            str(directory / 'main.cpp'), str(OWNER / 'src/launcher_projection.cpp'),
                            '-o', str(executable)], check=True)
            subprocess.run([str(executable)], check=True)


if __name__ == '__main__':
    unittest.main()
