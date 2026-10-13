"""Execute production Native/Runtime pause notification adapters and compatibility paths."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class LifecycleCallbackContractTest(unittest.TestCase):
    def test_named_snapshot_preference_fallback_and_errors(self):
        with tempfile.TemporaryDirectory(prefix='lifecycle-contract-') as directory:
            work = Path(directory)
            core = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                           ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                           work / 'core')
            types = (core / 'include/brookesia/system_core/app/types.hpp').read_text()
            reasons = types[types.index('struct AppPauseReasons {'):types.index('// Identity belongs')]
            source = (core / 'src/app/app.cpp').read_text()
            native = source[source.index('std::expected<void, std::string> IApp::on_pause_reasons_changed('):
                            source.index('std::optional<AppExecutionState> SystemApi::execution_state(')]
            source = (core / 'src/runtime/runtime.cpp').read_text()
            runtime = source[source.index('std::expected<void, std::string> System::Impl::call_runtime_pause_reasons_changed('):
                             source.index('std::expected<void, std::string> System::Impl::ensure_runtime_loaded(')]
            bridge = (ROOT / 'firmware/managed_components/espressif__brookesia_runtime_manager/include/brookesia/runtime_manager/types.hpp').read_text()
            values = bridge[bridge.index('using NativeValue ='):bridge.index('struct NativeFunctionSpec {')]
            cpp = work / 'test.cpp'
            cpp.write_text(r'''
#include <cassert>
#include <cstdint>
#include <expected>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>
#include <boost/json/src.hpp>
''' + reasons + r'''
struct AppContext {};
class IApp {
public:
 virtual ~IApp()=default;
 virtual std::expected<void,std::string> on_pause_reasons_changed(AppContext&,const AppPauseReasons&);
 virtual std::expected<void,std::string> on_suspension_changed(AppContext&);
};
''' + native + r'''
namespace runtime {
''' + values + r'''
}
struct Call {std::string name;runtime::NativeArgs args;};
struct Runtime {
 std::vector<Call> calls;std::map<std::string,runtime::NativeResult> results;
 runtime::NativeResult call_function(int,std::string_view module,std::string_view name,const runtime::NativeArgs&args){
  assert(module=="brookesia_app");calls.push_back({std::string(name),args});
  auto found=results.find(std::string(name));
  if(found==results.end())return std::unexpected("JavaScript function not found");
  return found->second;
 }
};
constexpr auto APP_MODULE_NAME="brookesia_app";
struct System {struct Impl {
 struct AppRecord{std::optional<int>runtime_app_id=3;};
 std::shared_ptr<Runtime>runtime_=std::make_shared<Runtime>();
 std::expected<void,std::string>call_runtime_pause_reasons_changed(AppRecord&,const AppPauseReasons&);
};};
''' + runtime + r'''
struct Legacy final:IApp {
 int calls=0;bool fail=false;
 std::expected<void,std::string>on_suspension_changed(AppContext&)override{
  ++calls;if(fail)return std::unexpected("legacy failure");return {};
 }
};
struct Modern final:IApp {
 int modern=0,legacy=0;AppPauseReasons received;
 std::expected<void,std::string>on_pause_reasons_changed(AppContext&,const AppPauseReasons&r)override{
  ++modern;received=r;return {};
 }
 std::expected<void,std::string>on_suspension_changed(AppContext&)override{++legacy;return {};}
};
int main(){
 AppContext context;AppPauseReasons reasons{true,true,false};
 IApp base;assert(base.on_pause_reasons_changed(context,reasons));
 Legacy legacy;assert(legacy.on_pause_reasons_changed(context,reasons));assert(legacy.calls==1);
 legacy.fail=true;assert(!legacy.on_pause_reasons_changed(context,reasons));assert(legacy.calls==2);
 Modern modern;assert(modern.on_pause_reasons_changed(context,reasons));
 assert(modern.modern==1 && modern.legacy==0 && modern.received.covered && modern.received.screen_off);
 System::Impl owner;System::Impl::AppRecord record;auto rt=owner.runtime_;
 rt->results["on_pause_reasons_changed"]=true;rt->results["on_suspension_changed"]=true;
 assert(owner.call_runtime_pause_reasons_changed(record,reasons));assert(rt->calls.size()==1);
 auto snapshot=boost::json::parse(std::get<std::string>(rt->calls.back().args[0])).as_object();
 assert(snapshot.size()==3 && snapshot.at("covered").as_bool() && snapshot.at("screen_off").as_bool());
 assert(!snapshot.at("manual_pause").as_bool());
 for(auto fields:{AppPauseReasons{true,false,false},AppPauseReasons{false,true,false},AppPauseReasons{false,false,true}}){
  rt->calls.clear();assert(owner.call_runtime_pause_reasons_changed(record,fields));
  auto value=boost::json::parse(std::get<std::string>(rt->calls.back().args[0])).as_object();
  assert(value.at("covered").as_bool()==fields.covered && value.at("screen_off").as_bool()==fields.screen_off);
  assert(value.at("manual_pause").as_bool()==fields.manual_pause);
 }
 rt->results.erase("on_pause_reasons_changed");rt->calls.clear();
 assert(owner.call_runtime_pause_reasons_changed(record,reasons));assert(rt->calls.size()==2);
 assert(rt->calls.back().name=="on_suspension_changed" && rt->calls.back().args.size()==3);
 assert(std::get<bool>(rt->calls.back().args[0]) && std::get<bool>(rt->calls.back().args[1]));
 assert(!std::get<bool>(rt->calls.back().args[2]));
 for(auto fields:{AppPauseReasons{true,false,false},AppPauseReasons{false,true,false},AppPauseReasons{false,false,true}}){
  rt->calls.clear();assert(owner.call_runtime_pause_reasons_changed(record,fields));
  const auto&args=rt->calls.back().args;
  assert(std::get<bool>(args[0])==fields.covered && std::get<bool>(args[1])==fields.screen_off);
  assert(std::get<bool>(args[2])==fields.manual_pause);
 }
 rt->results.clear();rt->calls.clear();assert(owner.call_runtime_pause_reasons_changed(record,reasons));
 assert(rt->calls.size()==2); // Old packages without either optional hook remain valid.
 rt->results["on_pause_reasons_changed"]=false;rt->calls.clear();
 assert(!owner.call_runtime_pause_reasons_changed(record,reasons));assert(rt->calls.size()==1);
 for(auto error:{"sensor not found","JavaScript app not found","JavaScript module not found"}){
  rt->results["on_pause_reasons_changed"]=std::unexpected(error);rt->calls.clear();
  auto result=owner.call_runtime_pause_reasons_changed(record,reasons);
  assert(!result && result.error()==error && rt->calls.size()==1);
 }
 rt->results.clear();rt->results["on_suspension_changed"]=false;
 assert(!owner.call_runtime_pause_reasons_changed(record,reasons));
 rt->results["on_suspension_changed"]=std::unexpected("legacy callback failed");
 auto result=owner.call_runtime_pause_reasons_changed(record,reasons);
 assert(!result && result.error()=="legacy callback failed");
 rt->results.clear();rt->results["on_pause_reasons_changed"]=std::unexpected("JavaScript host function not found");
 rt->results["on_suspension_changed"]=true;assert(owner.call_runtime_pause_reasons_changed(record,reasons));
 rt->calls.clear();record.runtime_app_id.reset();assert(owner.call_runtime_pause_reasons_changed(record,reasons));
 assert(rt->calls.empty());
}
''')
            binary = work / 'test'
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-DBOOST_NO_USER_CONFIG',
                            '-I' + str(ROOT / 'firmware/managed_components/espressif__esp-boost/src'),
                            str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)


if __name__ == '__main__':
    unittest.main()
