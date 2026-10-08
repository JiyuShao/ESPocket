#include "shell_overlay_internal.hpp"
namespace espocket {
std::expected<void,std::string> CircularShell::on_start(esp_brookesia::system::core::AppContext& context){
 context_=&context;home_gesture_state_=std::make_shared<HomeGestureState>();
 keyboard_state_=std::make_shared<KeyboardState>();message_dialog_state_=std::make_shared<MessageDialogState>();
 loading_state_=std::make_shared<LoadingState>();back_overlay_state_=std::make_shared<BackOverlayState>();home_intent_timer_id_=1;return {};
}
esp_brookesia::system::core::AppManifest CircularShell::get_manifest()const{return {};}
esp_brookesia::system::core::AppGuiDescriptor CircularShell::get_gui_descriptor()const{return {};}
std::expected<void,std::string> CircularShell::on_action(esp_brookesia::system::core::AppContext&,std::string_view){return {};}
uint32_t CircularShell::theme_color(std::string_view token)const{assert(!token.empty());return 0x123456;}
void CircularShell::cancel_gesture_input(){reset_shell_gesture(*home_gesture_state_,true);}
void CircularShell::sync_default_back(bool){}void CircularShell::sync_card_hint(bool){}
void CircularShell::stop_status(){}void CircularShell::stop_launcher(){}
void CircularShell::refresh_status(){}void CircularShell::refresh_launcher(){}void CircularShell::dispatch_launcher(){}
std::expected<void,std::string> CircularShell::show_launcher_page(size_t){return {};}
void CircularShell::set_status_text(std::string_view,std::string){}
std::expected<void,std::string> CircularShell::show_watch_face(){return show_surface(ShellSurface::WatchFace);}
}
