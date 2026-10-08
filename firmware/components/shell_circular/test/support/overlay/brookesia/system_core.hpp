#pragma once
#include <cstdint>
#include <expected>
#include <string>
#include <string_view>
#include <vector>
namespace esp_brookesia {
namespace gui {struct ScopedConnection {};}
namespace system::core {
using AppId=uint32_t;using TimerId=uint32_t;using MessageDialogRequestId=uint64_t;using KeyboardRequestId=uint64_t;
constexpr AppId INVALID_APP_ID=0;constexpr TimerId INVALID_TIMER_ID=0;
constexpr KeyboardRequestId INVALID_KEYBOARD_REQUEST_ID=0;constexpr MessageDialogRequestId INVALID_MESSAGE_DIALOG_REQUEST_ID=0;
enum class MessageDialogCloseReason {Button,Timeout,Closed};
enum class MessageDialogIcon {None,Information,Question,Warning,Critical};
enum class MessageDialogButtonRole {Action,Destructive};
struct MessageDialogButton {std::string text;MessageDialogButtonRole role=MessageDialogButtonRole::Action;};
struct MessageDialogOptions {std::string text,informative_text;MessageDialogIcon icon=MessageDialogIcon::None;std::vector<MessageDialogButton> buttons;int32_t auto_close_ms=0;};
struct KeyboardRequestOptions {std::string mode="text",title,initial_text,placeholder;std::vector<std::string> allowed_modes;int32_t max_length=0;bool password=false;};
struct AppManifest {};struct AppGuiDescriptor {};
struct AppContext {struct Timer {void stop(TimerId){}} t;Timer& timer(){return t;}struct Gui {bool fail=false;int base_transitions=0;bool quick=false;std::expected<void,std::string> trigger_screen_flow(std::string_view flow,std::string_view action){if(fail)return std::unexpected("gui failure");if(flow=="shell_pages")++base_transitions;else quick=action=="open_quick_settings";return {};}} g;Gui& gui(){return g;}};
struct IApp {virtual ~IApp()=default;virtual AppManifest get_manifest()const=0;virtual AppGuiDescriptor get_gui_descriptor()const=0;virtual std::expected<void,std::string> on_start(AppContext&)=0;virtual std::expected<void,std::string> on_stop(AppContext&)=0;virtual std::expected<void,std::string> on_action(AppContext&,std::string_view)=0;virtual std::expected<void,std::string> on_timer(AppContext&,TimerId,std::string_view)=0;};
}}
