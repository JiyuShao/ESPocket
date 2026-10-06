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
        retain = internal[internal.index('template<class State>\nvoid retain_overlay_userdata'):internal.index('extern const char shell_gui_json_start')]
        loading_state = internal[internal.index('struct CircularShell::LoadingState {'):internal.index('struct CircularShell::KeyboardState {')]
        keyboard_state = internal[internal.index('struct CircularShell::KeyboardState {'):internal.index('struct CircularShell::MessageDialogState {')]
        keyboard = (COMPONENT / 'src/shell_keyboard.cpp').read_text()
        keyboard = 'namespace espocket {\n' + keyboard[keyboard.index('void CircularShell::hide_keyboard('):]
        navigation = (COMPONENT / 'src/shell_navigation.cpp').read_text()
        display = navigation[navigation.index('std::expected<void, std::string> CircularShell::set_display_on('):navigation.index('} // namespace espocket', navigation.index('std::expected<void, std::string> CircularShell::set_display_on('))]
        lifecycle = (COMPONENT / 'src/circular_shell.cpp').read_text()
        stop = lifecycle[lifecycle.index('std::expected<void, std::string> CircularShell::on_stop('):lifecycle.index('std::expected<void, std::string> CircularShell::on_action(')]
        timer = (COMPONENT / 'src/circular_shell.cpp').read_text()
        timer = timer[timer.index('        // Consume recognized PWR'):timer.index('        refresh_launcher();', timer.index('        // Consume recognized PWR'))]
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
using AppId=uint32_t;using MessageDialogRequestId=uint64_t;using KeyboardRequestId=uint64_t;
constexpr KeyboardRequestId INVALID_KEYBOARD_REQUEST_ID=0;
constexpr int INVALID_TIMER_ID=0;
struct AppContext {struct Timer {void stop(int){}} t;Timer& timer(){return t;}};
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
struct lv_event_t {void* data;void* target=nullptr;void* current=nullptr;};
struct lv_obj_t {void(*destroy)(lv_event_t*)=nullptr;void* destroy_data=nullptr;std::vector<lv_obj_t*> children;bool deleted=false;void(*click)(lv_event_t*)=nullptr;void* data=nullptr;std::string text;int width=0,height=0,bg_opa=-1,max_height=0;};
std::vector<std::unique_ptr<lv_obj_t>> allocated;
int fail_after=-1,lock_depth=0,lock_calls=0;bool lock_fail=false;int64_t now=0;
int64_t esp_timer_get_time() {return now;}
constexpr int LV_OBJ_FLAG_HIDDEN=1,LV_INDEV_TYPE_POINTER=1,LV_OBJ_FLAG_CLICKABLE=2,LV_ALIGN_BOTTOM_MID=3;
int lv_font_montserrat_20=0;
void lv_obj_add_flag(lv_obj_t* o,int){o->bg_opa=0;}
bool lv_obj_is_valid(lv_obj_t* o){return o && !o->deleted;}
struct lv_indev_t {};
lv_indev_t* lv_indev_get_next(lv_indev_t*){return nullptr;}
int lv_indev_get_type(lv_indev_t*){return LV_INDEV_TYPE_POINTER;}
void lv_indev_enable(lv_indev_t*,bool){}

struct LvglLock {bool held=!lock_fail;LvglLock(){++lock_calls;if(held)++lock_depth;}~LvglLock(){if(held)--lock_depth;}
    explicit operator bool() const {return held;}};
lv_obj_t layer;
lv_obj_t* lv_layer_top(){return &layer;}
lv_obj_t* lv_obj_create(lv_obj_t* parent){if(fail_after==0)return nullptr;if(fail_after>0)--fail_after;
    allocated.push_back(std::make_unique<lv_obj_t>());auto* o=allocated.back().get();parent->children.push_back(o);return o;}
auto lv_label_create=lv_obj_create;auto lv_button_create=lv_obj_create;
void lv_obj_delete(lv_obj_t* o){o->deleted=true;for(auto* child:o->children)lv_obj_delete(child);if(o->destroy){lv_event_t e{o->destroy_data};o->destroy(&e);}}
void lv_label_set_text(lv_obj_t* o,const char* text){o->text=text;}
void* lv_event_get_user_data(lv_event_t* e){return e->data;}
void* lv_event_get_target(lv_event_t* e){return e->target;}
void* lv_event_get_current_target(lv_event_t* e){return e->current;}
constexpr int LV_EVENT_DELETE=99;
void lv_obj_add_event_cb(lv_obj_t* o,void(*cb)(lv_event_t*),int code,void* data){if(code==LV_EVENT_DELETE){o->destroy=cb;o->destroy_data=data;}else{o->click=cb;o->data=data;}}
void click(lv_obj_t* o){assert(!o->deleted && o->click);lv_event_t e{o->data};o->click(&e);}
int lv_pct(int n){return n;}int lv_color_hex(int n){return n;}int lv_font_montserrat_18=0;
constexpr int LV_OBJ_FLAG_SCROLLABLE=0,LV_OPA_80=0,LV_OPA_COVER=255,LV_OPA_TRANSP=0,LV_SIZE_CONTENT=-1,
    LV_FLEX_FLOW_COLUMN=0,LV_LABEL_LONG_MODE_WRAP=0,LV_LABEL_LONG_MODE_DOTS=0,LV_TEXT_ALIGN_CENTER=0,LV_EVENT_CLICKED=0,LV_STATE_PRESSED=1;
'''
        harness += '''
void lv_obj_set_size(lv_obj_t* o,int w,int h){o->width=w;o->height=h;}
void lv_obj_set_height(lv_obj_t* o,int h){o->height=h;}
void lv_obj_set_style_max_height(lv_obj_t* o,int h,int){o->max_height=h;}
void lv_obj_set_style_bg_opa(lv_obj_t* o,int opacity,int){o->bg_opa=opacity;}
'''
        for name in ('lv_obj_align', 'lv_obj_move_to_index', 'lv_obj_remove_flag', 'lv_obj_center', 'lv_obj_set_style_bg_color',
                     'lv_obj_set_style_border_width', 'lv_obj_set_style_radius',
                     'lv_obj_set_style_pad_all', 'lv_obj_set_style_pad_row', 'lv_obj_set_flex_flow',
                     'lv_obj_set_width', 'lv_obj_set_flex_grow', 'lv_label_set_long_mode',
                     'lv_obj_set_style_text_color', 'lv_obj_set_style_text_font', 'lv_obj_set_style_text_align'):
            harness += f'template<class... T> void {name}(T...) {{}}\n'
        harness += r'''
''' + retain + r'''
namespace espocket {
struct Gui {std::string theme="light";std::string get_theme(){return theme;}};struct Context {Gui g;Gui& gui(){return g;}};
enum class ShellSurface {WatchFace,LeftAppCard,RightAppCard};
struct Gesture {std::atomic_bool modal_active=false;std::atomic_bool keyboard_active=false;};
void reset_shell_gesture(Gesture&, bool) {}
struct CircularShell {
    struct PointerClickFilters {void remove(){}};
    std::shared_ptr<PointerClickFilters> pointer_click_filters_;
    uint32_t theme_color(std::string_view token) const {
        assert(!token.empty());
        return 0x123456;
    }
    struct LoadingState;struct KeyboardState;struct MessageDialogState;
    std::shared_ptr<LoadingState> loading_state_;
    std::expected<void,std::string> show_loading(AppId,bool startup=false);void hide_loading(AppId,bool startup=false);
    std::shared_ptr<KeyboardState> keyboard_state_;
    struct Back {std::atomic_bool clicked=false;lv_obj_t *button=nullptr,*card_hint=nullptr;};
    struct Connection {bool disconnected=false;void disconnect(){disconnected=true;}} gesture_connection_;
    struct Binding {bool released=false;void release(){released=true;}} display_binding_;
    int home_intent_timer_id_=0;
    std::shared_ptr<int> callback_state_;
    bool launcher_stopped=false,status_stopped=false;
    void stop_launcher(){launcher_stopped=true;}void stop_status(){status_stopped=true;}
    std::expected<void,std::string> on_stop(AppContext&);
    std::shared_ptr<Back> back_overlay_state_;
    int64_t last_activity_us_=0;bool screen_timeout_latched_=false;
    void cancel_gesture_input(){}
    ShellSurface current_surface(){return ShellSurface::WatchFace;}
    void sync_default_back(bool){}void sync_card_hint(bool){}
    void discard_overlay_choices();bool cancel_keyboard_input();
    void hide_keyboard(AppId,KeyboardRequestId);void poll_keyboard();
    std::expected<void,std::string> set_display_on(bool);
    void tick();void refresh_overlay_input();

    Context* context_=nullptr;std::shared_ptr<MessageDialogState> message_dialog_state_;
    std::shared_ptr<Gesture> home_gesture_state_=std::make_shared<Gesture>();
    void suspend_keyboard_input(bool);
    struct {std::function<void(AppId,MessageDialogRequestId,int32_t,MessageDialogCloseReason)> message_dialog_result;
        std::function<bool()> display_on,app_visible;
        std::function<void()> tick,expire_back,back;
        struct BackUi {bool default_visible=false;};std::function<BackUi()> back_ui;
        std::function<void(AppId,KeyboardRequestId,bool,std::string)> keyboard_result;
        std::function<bool(AppId,KeyboardRequestId)> keyboard_valid;
        std::function<bool(AppId,MessageDialogRequestId)> message_dialog_valid;} host_;
    std::expected<void,std::string> render_message_dialog(const MessageDialogOptions&);
    std::expected<void,std::string> show_message_dialog(AppId,MessageDialogRequestId,const MessageDialogOptions&);
    std::expected<void,std::string> update_message_dialog(AppId,MessageDialogRequestId,const MessageDialogOptions&);
    void hide_message_dialog(AppId,MessageDialogRequestId);void poll_message_dialog();
};
''' + loading_state + keyboard_state + state + '\n}\n' + actual + keyboard + '\nnamespace espocket {\n' + display + stop + '\nvoid CircularShell::tick(){\n' + timer + '\n}\n}\n' + r'''
int main(){
    using namespace espocket;
    CircularShell s;Context context;MessageDialogOptions opts;
    opts.text="Restart to apply theme?";opts.buttons={{"Restart"},{"Later"}};
    assert(!s.show_message_dialog(2,1,opts));
    s.context_=&context;s.message_dialog_state_=std::make_shared<CircularShell::MessageDialogState>();
    assert(s.show_message_dialog(2,1,opts));assert(s.home_gesture_state_->modal_active);
    auto* original=s.message_dialog_state_->overlay;
    auto* panel=original->children[0];
    assert(panel->width<=316 && panel->height==LV_SIZE_CONTENT);
    assert(panel->children[0]->max_height<=112);
    for(size_t i=1;i<panel->children.size();++i) assert(panel->children[i]->bg_opa==255);
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
    // Screen-off suppresses submission; invalidated failed hide cannot revive.
    assert(s.show_message_dialog(0,4,opts));
    button=s.message_dialog_state_->overlay->children[0]->children[1];click(button);
    s.host_.display_on=[] {return false;};s.poll_message_dialog();assert(calls==2);
    lock_fail=true;s.hide_message_dialog(0,4);assert(s.message_dialog_state_->invalidated);
    s.host_.display_on=[] {return true;};s.poll_message_dialog();assert(calls==2);
    lock_fail=false;s.hide_message_dialog(0,4);s.poll_message_dialog();assert(calls==2);
    // Actual display seam pauses presentation clock exactly across off/wake,
    // including an update received asleep. Owner hide still revokes immediately.
    now=20000;opts.auto_close_ms=10;
    assert(s.show_message_dialog(0,5,opts));assert(s.set_display_on(false));
    s.host_.display_on=[] {return false;};now=90000;s.poll_message_dialog();assert(calls==2);
    assert(s.update_message_dialog(0,5,opts));
    now=190000;assert(s.set_display_on(true));s.host_.display_on=[] {return true;};
    assert(s.message_dialog_state_->deadline_us==200000);
    s.hide_message_dialog(0,5);
    // A pre-existing keyboard keeps its textarea/draft while Dialog owns input.
    s.keyboard_state_=std::make_shared<CircularShell::KeyboardState>();
    auto keyboard_request=[&](uint64_t id) {
        auto &k=*s.keyboard_state_;k.app_id=8;k.request_id=id;k.invalidated=false;
        k.overlay=lv_obj_create(lv_layer_top());k.text_area=lv_label_create(k.overlay);
        k.text_area->text="draft";k.text="draft";k.confirmed=true;k.result_pending=true;
    };
    keyboard_request(10);auto* draft=s.keyboard_state_->text_area;
    assert(s.show_message_dialog(0,6,opts));s.poll_keyboard();
    assert(s.keyboard_state_->suspended && s.keyboard_state_->text_area==draft && draft->text=="draft");
    s.hide_keyboard(9,10);assert(s.keyboard_state_->request_id==10);
    s.hide_message_dialog(0,6);s.refresh_overlay_input();assert(!s.keyboard_state_->suspended);
    int keyboard_calls=0;
    s.host_.keyboard_result=[&](AppId app,KeyboardRequestId id,bool confirmed,std::string text) {
        assert(lock_depth==0 && app==8 && id==10 && confirmed && text=="draft");++keyboard_calls;
    };
    lock_fail=true;s.poll_keyboard();assert(keyboard_calls==0 && s.keyboard_state_->result_pending);
    lock_fail=false;s.poll_keyboard();s.poll_keyboard();assert(keyboard_calls==1);
    // Default and Edge Back both reach cancel_keyboard_input; page Back stays untouched.
    keyboard_request(11);assert(s.cancel_keyboard_input());
    s.host_.keyboard_result=[&](AppId,KeyboardRequestId id,bool confirmed,std::string text) {
        assert(id==11 && !confirmed && text.empty());++keyboard_calls;
    };
    s.poll_keyboard();assert(keyboard_calls==2);assert(!s.cancel_keyboard_input());
    // Run the real Owner tick prefix: recognized PWR clears unsubmitted results,
    // while a system-owned Dialog remains. Already submitted effects stay counted.
    keyboard_request(12);assert(s.show_message_dialog(0,7,opts));
    button=s.message_dialog_state_->overlay->children[0]->children[1];click(button);
    s.host_.tick=[&] {s.discard_overlay_choices();s.hide_keyboard(8,12);};
    s.tick();assert(keyboard_calls==2 && calls==2 && s.message_dialog_state_->request_id==7);
    assert(!s.message_dialog_state_->result_pending);
    // A revoked request whose GUI hide fails must never deliver a late result.
    lock_fail=true;s.hide_message_dialog(0,7);s.tick();assert(calls==2);
    lock_fail=false;s.tick();assert(!s.message_dialog_state_->overlay && calls==2);
    s.host_.tick={};
    s.loading_state_=std::make_shared<CircularShell::LoadingState>();
    assert(s.show_loading(8));assert(s.show_loading(8));assert(!s.show_loading(9));
    s.hide_loading(9);assert(s.loading_state_->overlay);
    lock_fail=true;s.hide_loading(8);assert(s.loading_state_->invalidated);
    lock_fail=false;s.tick();assert(!s.loading_state_->overlay);
    assert(s.show_loading(8,true));assert(s.show_loading(8));
    s.hide_loading(8,true);assert(s.loading_state_->overlay); // App explicitly waits beyond startup.
    s.hide_loading(8);assert(!s.loading_state_->overlay);
    const auto loading_closed_locks=lock_calls;
    for(int i=0;i<5;++i)s.tick();
    assert(lock_calls==loading_closed_locks); // Successful cleanup must not retry on every 50 ms tick.
    s.hide_loading(INVALID_APP_ID);assert(lock_calls==loading_closed_locks);
    fail_after=0;assert(!s.show_loading(8));fail_after=-1;
    // Real userdata-retention helper keeps revoked callback storage alive until
    // GUI deletion, even if the Shell releases its own reference after failure.
    auto callback_state=std::make_shared<int>(42);std::weak_ptr<int> weak=callback_state;
    auto* retained_view=lv_obj_create(lv_layer_top());retain_overlay_userdata(retained_view,callback_state);
    callback_state.reset();assert(!weak.expired());
    lv_event_t bubbled{retained_view->destroy_data,&layer,retained_view};retained_view->destroy(&bubbled);
    assert(!weak.expired());lv_obj_delete(retained_view);assert(weak.expired());
    // Core can revoke while GUI hide is still deferred: validate without LVGL,
    // then keep the old keyboard hidden and suppress its late pending result.
    keyboard_request(14);assert(s.show_message_dialog(0,9,opts));
    s.host_.keyboard_valid=[](AppId,KeyboardRequestId id){assert(lock_depth==0);return id!=14;};
    lock_fail=true;s.hide_message_dialog(0,9);s.refresh_overlay_input();
    assert(s.keyboard_state_->invalidated && s.keyboard_state_->suspended);
    lock_fail=false;s.tick();assert(s.keyboard_state_->request_id==0 && keyboard_calls==2);
    s.host_.keyboard_valid={};
    // Before the deferred old hide arrives, the next Core Dialog must replace
    // the revoked presentation instead of failing because its GUI still exists.
    assert(s.show_message_dialog(0,10,opts));
    s.host_.message_dialog_valid=[](AppId,MessageDialogRequestId id){assert(lock_depth==0);return id!=10;};
    assert(s.show_message_dialog(0,11,opts));assert(s.message_dialog_state_->request_id==11);
    s.hide_message_dialog(0,10);assert(s.message_dialog_state_->request_id==11);
    s.hide_message_dialog(0,11);s.host_.message_dialog_valid={};
    // Actual stop must continue stopping all bindings/input even if the first
    // Loading hide fails. All other Overlay userdata remains revoked and safe.
    keyboard_request(13);assert(s.show_message_dialog(0,8,opts));assert(s.show_loading(8));
    auto old_keyboard=s.keyboard_state_;auto old_dialog=s.message_dialog_state_;
    AppContext stop_context;lock_fail=true;
    assert(!s.on_stop(stop_context));
    assert(s.launcher_stopped && s.status_stopped && s.gesture_connection_.disconnected && s.display_binding_.released);
    assert(!s.context_ && old_keyboard->invalidated && old_dialog->invalidated);
    s.host_.keyboard_result=[&](AppId,KeyboardRequestId,bool,std::string){assert(false);};
    s.host_.message_dialog_result=[&](AppId,MessageDialogRequestId,int32_t,MessageDialogCloseReason){assert(false);};
    s.poll_keyboard();s.poll_message_dialog();
    lock_fail=false;assert(s.on_stop(stop_context)); // Cleanup retry releases the original state.
    assert(!s.keyboard_state_ && !s.message_dialog_state_);
    s.context_=&context;s.message_dialog_state_=std::make_shared<CircularShell::MessageDialogState>();
    s.home_gesture_state_=std::make_shared<Gesture>();
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
