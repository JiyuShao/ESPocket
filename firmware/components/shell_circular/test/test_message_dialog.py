"""Execute Shell presentation with a fake LVGL sink; Core keeps request ownership."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]


class MessageDialogTest(unittest.TestCase):
    def test_owner_update_completion_timeout_and_render_failure(self):
        internal = (COMPONENT / 'src/shell_internal.hpp').read_text()
        state = internal[internal.index('struct CircularShell::MessageDialogState {'):internal.index('struct CircularShell::BackOverlayState {')]
        actual = (COMPONENT / 'src/shell_message_dialog.cpp').read_text().replace('#include "shell_internal.hpp"', '')
        harness = r'''
#include <array>
#include <atomic>
#include <cassert>
#include <cinttypes>
#include <expected>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
namespace esp_brookesia::system::core {
using AppId=uint32_t;using MessageDialogRequestId=uint64_t;
constexpr AppId INVALID_APP_ID=0;constexpr MessageDialogRequestId INVALID_MESSAGE_DIALOG_REQUEST_ID=0;
enum class MessageDialogCloseReason {Button,Timeout,Closed};
enum class MessageDialogIcon {None,Information,Question,Warning,Critical};
enum class MessageDialogButtonRole {Action,Destructive};
struct MessageDialogButton {std::string text;MessageDialogButtonRole role=MessageDialogButtonRole::Action;};
struct MessageDialogOptions {std::string text,informative_text;MessageDialogIcon icon=MessageDialogIcon::None;
    std::vector<MessageDialogButton> buttons;int32_t auto_close_ms=0;};
}
using namespace esp_brookesia::system::core;
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
struct lv_event_t {void* data;};
struct lv_obj_t {std::vector<lv_obj_t*> children;bool deleted=false;void(*click)(lv_event_t*)=nullptr;void* data=nullptr;std::string text;};
std::vector<std::unique_ptr<lv_obj_t>> allocated;
int fail_after=-1,lock_depth=0;bool lock_fail=false;int64_t now=0;
int64_t esp_timer_get_time() {return now;}
struct LvglLock {bool held=!lock_fail;LvglLock(){if(held)++lock_depth;}~LvglLock(){if(held)--lock_depth;}
    explicit operator bool() const {return held;}};
lv_obj_t layer;
lv_obj_t* lv_layer_top(){return &layer;}
lv_obj_t* lv_obj_create(lv_obj_t* parent){if(fail_after==0)return nullptr;if(fail_after>0)--fail_after;
    allocated.push_back(std::make_unique<lv_obj_t>());auto* o=allocated.back().get();parent->children.push_back(o);return o;}
auto lv_label_create=lv_obj_create;auto lv_button_create=lv_obj_create;
void lv_obj_delete(lv_obj_t* o){o->deleted=true;for(auto* child:o->children)lv_obj_delete(child);}
void lv_label_set_text(lv_obj_t* o,const char* text){o->text=text;}
void* lv_event_get_user_data(lv_event_t* e){return e->data;}
void lv_obj_add_event_cb(lv_obj_t* o,void(*cb)(lv_event_t*),int,void* data){o->click=cb;o->data=data;}
void click(lv_obj_t* o){assert(!o->deleted && o->click);lv_event_t e{o->data};o->click(&e);}
int lv_pct(int n){return n;}int lv_color_hex(int n){return n;}int lv_font_montserrat_18=0;
constexpr int LV_OBJ_FLAG_SCROLLABLE=0,LV_OPA_80=0,LV_OPA_COVER=0,LV_OPA_TRANSP=0,
    LV_FLEX_FLOW_COLUMN=0,LV_LABEL_LONG_MODE_WRAP=0,LV_LABEL_LONG_MODE_DOTS=0,LV_TEXT_ALIGN_CENTER=0,LV_EVENT_CLICKED=0;
'''
        for name in ('lv_obj_remove_flag', 'lv_obj_set_size', 'lv_obj_center', 'lv_obj_set_style_bg_color',
                     'lv_obj_set_style_bg_opa', 'lv_obj_set_style_border_width', 'lv_obj_set_style_radius',
                     'lv_obj_set_style_pad_all', 'lv_obj_set_style_pad_row', 'lv_obj_set_flex_flow',
                     'lv_obj_set_width', 'lv_obj_set_flex_grow', 'lv_label_set_long_mode',
                     'lv_obj_set_style_text_color', 'lv_obj_set_style_text_font', 'lv_obj_set_style_text_align'):
            harness += f'template<class... T> void {name}(T...) {{}}\n'
        harness += r'''
namespace espocket {
struct Gui {std::string get_theme(){return "dark";}};struct Context {Gui g;Gui& gui(){return g;}};
struct Gesture {std::atomic_bool modal_active=false;};
struct CircularShell {
    struct MessageDialogState;
    Context* context_=nullptr;std::shared_ptr<MessageDialogState> message_dialog_state_;
    std::shared_ptr<Gesture> home_gesture_state_=std::make_shared<Gesture>();
    struct {std::function<void(AppId,MessageDialogRequestId,int32_t,MessageDialogCloseReason)> message_dialog_result;} host_;
    std::expected<void,std::string> render_message_dialog(const MessageDialogOptions&);
    std::expected<void,std::string> show_message_dialog(AppId,MessageDialogRequestId,const MessageDialogOptions&);
    std::expected<void,std::string> update_message_dialog(AppId,MessageDialogRequestId,const MessageDialogOptions&);
    void hide_message_dialog(AppId,MessageDialogRequestId);void poll_message_dialog();
};
''' + state + '\n}\n' + actual + r'''
int main(){
    using namespace espocket;
    CircularShell s;Context context;MessageDialogOptions opts;
    opts.text="Restart to apply theme?";opts.buttons={{"Restart"},{"Later"}};
    assert(!s.show_message_dialog(2,1,opts));
    s.context_=&context;s.message_dialog_state_=std::make_shared<CircularShell::MessageDialogState>();
    assert(s.show_message_dialog(2,1,opts));assert(s.home_gesture_state_->modal_active);
    auto* original=s.message_dialog_state_->overlay;
    assert(!s.show_message_dialog(3,2,opts));assert(!s.update_message_dialog(3,1,opts));
    s.hide_message_dialog(3,1);s.hide_message_dialog(2,2);assert(!original->deleted);
    fail_after=2;assert(!s.update_message_dialog(2,1,opts));fail_after=-1;assert(!original->deleted);
    assert(s.update_message_dialog(2,1,opts));assert(original->deleted);
    auto* button=s.message_dialog_state_->overlay->children[0]->children[2];
    int calls=0;
    s.host_.message_dialog_result=[&](AppId app,MessageDialogRequestId id,int32_t index,MessageDialogCloseReason reason){
        assert(lock_depth==0);assert(app==2 && id==1 && index==1 && reason==MessageDialogCloseReason::Button);
        assert(!s.message_dialog_state_->overlay);++calls;};
    click(button);click(button);assert(calls==0);
    lock_fail=true;s.poll_message_dialog();assert(calls==0 && s.message_dialog_state_->overlay);
    lock_fail=false;s.poll_message_dialog();s.poll_message_dialog();assert(calls==1);
    assert(!s.home_gesture_state_->modal_active);
    // The old App's hide cannot dismiss a new owner's queued presentation.
    opts.auto_close_ms=10;assert(s.show_message_dialog(3,2,opts));s.hide_message_dialog(2,1);
    assert(s.message_dialog_state_->overlay);
    s.host_.message_dialog_result=[&](AppId app,MessageDialogRequestId id,int32_t index,MessageDialogCloseReason reason){
        assert(lock_depth==0 && app==3 && id==2 && index==-1 && reason==MessageDialogCloseReason::Timeout);++calls;};
    now=9999;s.poll_message_dialog();assert(calls==1);now=10000;s.poll_message_dialog();assert(calls==2);
    // Core-initiated close (PWR/App stop) drops pending selection without completion.
    assert(s.show_message_dialog(4,3,opts));button=s.message_dialog_state_->overlay->children[0]->children[1];
    click(button);s.hide_message_dialog(4,3);s.poll_message_dialog();assert(calls==2);
    opts.buttons.resize(4);assert(!s.show_message_dialog(4,4,opts));
    opts.buttons.clear();opts.auto_close_ms=-1;assert(!s.show_message_dialog(4,4,opts));
    opts.auto_close_ms=0;lock_fail=true;assert(!s.show_message_dialog(4,4,opts));
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-message-dialog-') as directory:
            cpp = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            cpp.write_text(harness)
            subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', str(cpp), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=10)
