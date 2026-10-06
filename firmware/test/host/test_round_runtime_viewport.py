"""Exercise product geometry and real backend mount/unmount coordinate ownership."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PRESENTATION_HEADER = ROOT / 'firmware/components/espocket_system/src/round_presentation.hpp'
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare


class RoundRuntimeViewportTest(unittest.TestCase):
    def test_environment_query_uses_calling_app_and_current_language(self):
        with tempfile.TemporaryDirectory(prefix='round-environment-') as directory:
            temporary = Path(directory)
            core = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_system_core',
                           ROOT / 'firmware/patches/espressif__brookesia_system_core/0.8.4/manifest.json',
                           temporary / 'core')
            manager = (core / 'src/app/manager.cpp').read_text()
            start = manager.index('boost::json::object System::get_environment_json(')
            query = manager[start:manager.index('\n} // namespace', start)]
            service = (core / 'src/service/system.cpp').read_text()
            start = service.index('FunctionResult SystemService::get_environment()')
            rpc = service[start:service.index('FunctionResult SystemService::get_active_app()', start)]
            code = r'''
#include <cassert>
#include <cmath>
#include <expected>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <variant>
namespace boost::json {using object=std::map<std::string,std::variant<int,float,std::string>>;}
using AppId=int;
struct Environment{int width_px=466,height_px=466;float density=1,font_scale=1;std::string language="en",theme_id="default";};
struct Manifest{bool runtime;};
struct AppInfo{AppId app_id;Manifest manifest;};
struct System {
 struct Presentation{Environment environment;};
 struct Impl{Environment environment_;struct Config{std::function<Presentation(Manifest,Environment)>app_presentation;}config_;}owner;
 Impl*impl_=&owner;
 std::optional<AppInfo>get_app(AppId id)const{if(id==1||id==2)return AppInfo{id,{id==2}};return {};}
 boost::json::object get_environment_json(std::optional<AppId> = {})const;
};
using FunctionResult=std::expected<boost::json::object,std::string>;
FunctionResult make_success(boost::json::object value){return value;}
FunctionResult make_error(std::string error){return std::unexpected(error);}
std::expected<std::optional<AppInfo>,std::string> caller=std::optional<AppInfo>{};
auto get_runtime_caller(System&){return caller;}
struct SystemService{System&system_;FunctionResult get_environment();};
''' + query + rpc + r'''
int main(){
 System system;system.owner.config_.app_presentation=[](Manifest manifest,Environment environment){
  if(manifest.runtime){environment.width_px=329;environment.height_px=329;environment.density=329.0F/480;}
  return System::Presentation{environment};
 };
 SystemService service{system};
 assert(std::get<int>(service.get_environment()->at("width_px"))==466);
 caller=AppInfo{2,{true}};auto runtime=service.get_environment();
 assert(std::get<int>(runtime->at("width_px"))==329);
 assert(std::abs(329/std::get<float>(runtime->at("density"))-480)<0.001);
 system.owner.environment_.language="zh_CN";
 assert(std::get<std::string>(service.get_environment()->at("language"))=="zh_CN");
 caller=AppInfo{1,{false}};assert(std::get<int>(service.get_environment()->at("width_px"))==466);
 caller=std::unexpected("stale caller");assert(!service.get_environment());
 assert(std::get<int>(system.get_environment_json().at("width_px"))==466);
}
'''
            source = temporary / 'test.cpp'
            source.write_text(code)
            binary = temporary / 'test'
            compiled = subprocess.run(['c++', '-std=c++23', str(source), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_viewport_mount_input_coordinates_and_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='round-viewport-') as directory:
            temporary = Path(directory)
            component = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_gui_lvgl',
                                ROOT / 'firmware/patches/espressif__brookesia_gui_lvgl/0.8.5/manifest.json',
                                temporary / 'component')
            text = (component / 'src/backend.cpp').read_text()
            start = text.index('bool BackendImpl::mount_screen(')
            methods = text[start:text.index('bool BackendImpl::register_display(', start)]
            patched_interface = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_gui_interface',
                                        ROOT / 'firmware/patches/espressif__brookesia_gui_interface/0.8.2/manifest.json',
                                        temporary / 'interface')
            interface = (patched_interface / 'include/brookesia/gui_interface/document.hpp').read_text()
            start = interface.index('struct GuiViewport {')
            types = interface[start:interface.index('struct ResolvedFontSpec {', start)]
            code = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <map>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...)
#define BROOKESIA_LOGD(...)
#define BROOKESIA_LOGE(...)
#define BROOKESIA_DESCRIBE_ENUM_TO_STR(...) ""
enum class GuiLayer {Default}; enum class MountStackMode {Replace};
''' + types + r'''
struct lv_obj_t {lv_obj_t*parent=nullptr;int x=0,y=0,width=466,height=466;bool hidden=false;};
struct lv_display_t {};
constexpr int LV_OBJ_FLAG_HIDDEN=1,LV_OBJ_FLAG_SCROLLABLE=2,LV_OBJ_FLAG_CLICKABLE=4;
int containers=0;
auto*lv_obj_create(lv_obj_t*parent){++containers;auto*object=new lv_obj_t;object->parent=parent;return object;}
void lv_obj_delete(lv_obj_t*object){--containers;delete object;}
void lv_obj_set_parent(lv_obj_t*object,lv_obj_t*parent){object->parent=parent;}
auto*lv_obj_get_parent(lv_obj_t*object){return object->parent;}
bool lv_obj_is_valid(lv_obj_t*object){return object!=nullptr;}
void lv_obj_remove_style_all(lv_obj_t*){}
void lv_obj_remove_flag(lv_obj_t*object,int flags){if(flags&1)object->hidden=false;}
void lv_obj_add_flag(lv_obj_t*object,int flags){if(flags&1)object->hidden=true;}
void lv_obj_set_pos(lv_obj_t*object,int x,int y){object->x=x;object->y=y;}
void lv_obj_set_size(lv_obj_t*object,int width,int height){object->width=width;object->height=height;}
void lv_obj_move_foreground(lv_obj_t*){}
void lv_obj_update_layout(lv_obj_t*){}
int lv_display_get_horizontal_resolution(lv_display_t*){return 466;}
int lv_display_get_vertical_resolution(lv_display_t*){return 466;}
struct ThreadLockGuard {};
struct BackendHandle {using Value=unsigned;Value identity;explicit BackendHandle(Value value):identity(value){};Value value()const{return identity;}};
struct Record {bool is_top_level_screen=true;lv_obj_t*object;unsigned mount_refresh_subtree_count=1;struct FrameViewPayload{int props;};template<class Payload>Payload*get_type_payload(){return nullptr;}};
bool requires_mount_placement_reapply(const Record&){return true;}
enum class PlacementApplyMask {All};
struct BackendImpl {
 lv_obj_t layer,screen;lv_display_t display;Record record{true,&screen};
 std::unordered_map<unsigned,MountTarget> mounted_targets;
 std::unordered_map<unsigned,lv_obj_t*> mounted_viewports;
 Record*find_record(BackendHandle){return &record;}
 std::string resolve_display_id(const std::string&){return "display";}
 lv_display_t*resolve_display(const std::string&){return &display;}
 lv_obj_t*resolve_layer_parent(lv_display_t*,GuiLayer){return &layer;}
 void collect_mount_refresh_handles(BackendHandle handle,std::vector<unsigned>&handles){handles.push_back(handle.value());}
 bool mount_screen(BackendHandle,const MountTarget&);
 bool unmount_screen(BackendHandle);
};
namespace lvgl {
int get_record_placement(const Record&){return 0;}
void apply_placement(BackendImpl&,Record&record,int,PlacementApplyMask,bool){record.object->width=record.object->parent->width;record.object->height=record.object->parent->height;}
}
void refresh_frame_view(BackendImpl&,Record&,int){}
''' + methods + r'''
#include "PRODUCT_PRESENTATION"
int main(){
 BackendImpl backend;BackendHandle handle(1);MountTarget native;
 using namespace esp_brookesia;
 gui::Environment environment{466,466,1.0F};
 system::core::AppManifest manifest{system::core::AppKind::Native,{}};
 assert(!espocket::round_app_presentation(manifest,environment).viewport);
 manifest.kind=system::core::AppKind::Runtime;manifest.supported_systems={"espocket"};
 assert(!espocket::round_app_presentation(manifest,environment).viewport);
 manifest.supported_systems={"super"};
 auto presentation=espocket::round_app_presentation(manifest,environment);
 assert(presentation.viewport && presentation.viewport->width==329);
 assert(std::abs(presentation.environment.width_px/presentation.environment.density-480)<0.001);
 manifest.id="brookesia.general.ai_chatbot";
 manifest.version="0.2.1";
 auto landscape=espocket::round_app_presentation(manifest,environment);
 assert(landscape.viewport->width==329 && landscape.viewport->height==197);
 assert(landscape.viewport->x==68 && landscape.viewport->y==134);
 assert(std::abs(landscape.environment.width_px/landscape.environment.density-800)<0.001);
 assert(landscape.environment.height_px==landscape.viewport->height);
 manifest.version="0.3.0";
 assert(espocket::round_app_presentation(manifest,environment).viewport->height==329);
 manifest.id="";
 for(auto x:{presentation.viewport->x,presentation.viewport->x+presentation.viewport->width-1})
  for(auto y:{presentation.viewport->y,presentation.viewport->y+presentation.viewport->height-1})
   assert((x-232.5)*(x-232.5)+(y-232.5)*(y-232.5)<233*233);
 assert(backend.mount_screen(handle,native));assert(backend.screen.parent==&backend.layer);assert(backend.screen.width==466);assert(containers==0);
 MountTarget runtime;runtime.viewport=presentation.viewport;
 for(int iteration=0;iteration<100;++iteration){
  assert(backend.mount_screen(handle,runtime));assert(containers==1);assert(backend.screen.width==329);
  assert(backend.screen.parent->x==68 && backend.screen.parent->y==68);
  assert(backend.mounted_targets.at(1).viewport->width==329);
  assert(backend.mount_screen(handle,runtime));assert(containers==1);
  assert(backend.unmount_screen(handle));assert(containers==0);assert(backend.screen.hidden);
  assert(backend.screen.parent==&backend.layer);
 }
 runtime.viewport->x=300;assert(!backend.mount_screen(handle,runtime));assert(containers==0);
 assert(backend.mount_screen(handle,native));assert(backend.screen.width==466 && !backend.screen.hidden);
}
'''
            code = code.replace('PRODUCT_PRESENTATION', str(PRESENTATION_HEADER))
            header = temporary / 'brookesia/system_core/system/system.hpp'
            header.parent.mkdir(parents=True)
            header.write_text(r'''
#pragma once
namespace esp_brookesia {
namespace gui {using GuiViewport=::GuiViewport;struct Environment{int width_px,height_px;float density;};}
namespace system::core {
enum class AppKind {Native,Runtime};
struct AppManifest{AppKind kind;std::vector<std::string>supported_systems;std::string id,version;};
struct System{struct Config{struct AppPresentation{gui::Environment environment;std::optional<gui::GuiViewport>viewport;};};};
}
}
''')
            source = temporary / 'test.cpp'
            source.write_text(code)
            binary = temporary / 'test'
            compiled = subprocess.run(['c++', '-std=c++23', '-I', str(temporary), str(source), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
