#include "espocket/circular_shell.hpp"
#include "lvgl.h"
#include <set>
#include <tuple>
using namespace espocket;
using namespace esp_brookesia::system::core;

lv_obj_t* last_root(){
 for(auto it=layer.children.rbegin();it!=layer.children.rend();++it)if(!(*it)->deleted)return *it;
 assert(false);return nullptr;
}
lv_obj_t* button(lv_obj_t* dialog,size_t index=0){return dialog->children[0]->children[index+1];}
int main(){
 AppContext context;bool display=true,pwr=false,routing_fail=false;
 std::set<uint64_t> invalid_keys,invalid_dialogs;
 std::vector<std::tuple<AppId,uint64_t,int,MessageDialogCloseReason>> dialogs;
 std::vector<std::tuple<AppId,uint64_t,bool,std::string>> keys;
 int acquire=0,restore=0,drop=0,source_changes=0;
 CircularShell* instance=nullptr;
 ShellHost host;
 host.display_on=[&]{assert(lock_depth==0);return display;};
 host.keyboard_valid=[&](AppId,uint64_t id){assert(lock_depth==0);return !invalid_keys.contains(id);};
 host.message_dialog_valid=[&](AppId,uint64_t id){assert(lock_depth==0);return !invalid_dialogs.contains(id);};
 host.message_dialog_result=[&](auto app,auto id,auto index,auto reason){assert(lock_depth==0);dialogs.emplace_back(app,id,index,reason);};
 host.keyboard_result=[&](auto app,auto id,bool confirmed,std::string text){assert(lock_depth==0);keys.emplace_back(app,id,confirmed,text);};
 host.quick_settings_display=[&](bool on,bool back)->std::expected<void,std::string>{
  assert(lock_depth==0);if(routing_fail)return std::unexpected("display failed");
  if(on)++acquire;else if(back)++restore;else ++drop;return {};
 };
 host.surface_changed=[&](auto){++source_changes;};
 host.tick=[&]{if(pwr){instance->discard_overlay_choices();instance->hide_keyboard(8,13);pwr=false;}};
 CircularShell shell(1,host);instance=&shell;
 MessageDialogOptions options;options.text="Question";options.buttons={{"Yes"},{"No"}};
 KeyboardRequestOptions input;input.initial_text="draft";
 assert(!shell.show_keyboard(8,10,input));assert(shell.on_start(context));
 auto tick=[&]{assert(shell.on_timer(context,1,"espocket.home_intent"));};
 // Real renderers + actual QS interface preserve the same underlying page.
 assert(shell.show_surface(ShellSurface::LeftAppCard));int base=context.g.base_transitions;
 assert(shell.show_keyboard(8,10,input));auto* keyboard=last_root();auto* textarea=keyboard->children[1];
 assert(!keyboard->hidden && textarea->text=="draft");
 options.auto_close_ms=10;assert(shell.show_message_dialog(0,1,options));auto* dialog=last_root();
 assert(keyboard->hidden && !dialog->hidden);
 assert(shell.show_surface(ShellSurface::QuickSettings));assert(dialog->hidden && keyboard->hidden);
 assert(shell.underlying_surface()==ShellSurface::LeftAppCard && context.g.base_transitions==base);
 assert(shell.show_surface(ShellSurface::QuickSettings));assert(acquire==1);
 click(button(dialog));tick();assert(dialogs.empty()); // Covered callback cannot choose.
 now=10000;tick();assert(dialog->deleted && dialogs.size()==1);
 assert(std::get<3>(dialogs.back())==MessageDialogCloseReason::Timeout && keyboard->hidden);
 assert(shell.dismiss_quick_settings());assert(!keyboard->hidden && textarea->text=="draft");
 assert(restore==1 && context.g.base_transitions==base);
 // One keyboard completion, after successful GUI deletion; lock failure retries.
 ready(keyboard->children[2]);lock_fail=true;tick();assert(keys.empty() && !keyboard->deleted);
 lock_fail=false;tick();tick();assert(keys.size()==1 && keyboard->deleted);
 assert(std::get<2>(keys.back()) && std::get<3>(keys.back())=="draft");
 // Active Dialog resumes first. Wrong identity cannot hide/update current view.
 assert(shell.show_keyboard(8,11,input));keyboard=last_root();options.auto_close_ms=0;
 assert(shell.show_message_dialog(0,2,options));dialog=last_root();
 assert(!shell.update_message_dialog(8,2,options));shell.hide_message_dialog(0,1);assert(!dialog->deleted);
 assert(shell.show_surface(ShellSurface::QuickSettings));assert(shell.dismiss_quick_settings());
 assert(!dialog->hidden && keyboard->hidden);
 click(button(dialog,1));tick();assert(dialogs.size()==2 && std::get<2>(dialogs.back())==1);
 assert(dialog->deleted && !keyboard->hidden);
 // Covered expiry defeats an already queued unsubmitted choice.
 now=20000;options.auto_close_ms=10;assert(shell.show_message_dialog(0,3,options));dialog=last_root();
 click(button(dialog));assert(shell.show_surface(ShellSurface::QuickSettings));now=30000;tick();
 assert(dialogs.size()==3 && std::get<3>(dialogs.back())==MessageDialogCloseReason::Timeout);
 assert(shell.dismiss_quick_settings());
 // Revocation while covered: stale keyboard never returns or submits its draft.
 assert(shell.show_surface(ShellSurface::QuickSettings));invalid_keys.insert(11);
 lock_fail=true;tick();assert(!keyboard->deleted);lock_fail=false;tick();
 assert(keyboard->deleted && shell.dismiss_quick_settings());assert(keys.size()==1);
 // PWR consumes intent before either result delivery, while system Dialog stays.
 assert(shell.show_keyboard(8,13,input));keyboard=last_root();ready(keyboard->children[2]);
 options.auto_close_ms=0;assert(shell.show_message_dialog(0,4,options));dialog=last_root();click(button(dialog));
 pwr=true;tick();assert(keys.size()==1 && dialogs.size()==3 && keyboard->deleted && !dialog->deleted);
 // Failed external hide revokes old callbacks; cleanup retries without delivery.
 lock_fail=true;shell.hide_message_dialog(0,4);click(button(dialog));tick();assert(dialogs.size()==3);
 lock_fail=false;tick();assert(dialog->deleted && dialogs.size()==3);
 // GUI render failure preserves old view; update commits only complete render.
 assert(shell.show_message_dialog(0,5,options));dialog=last_root();fail_after=2;
 assert(!shell.update_message_dialog(0,5,options));assert(!dialog->deleted);fail_after=-1;
 assert(shell.update_message_dialog(0,5,options));assert(dialog->deleted);dialog=last_root();
 // A revoked view awaiting deletion cannot trap the next valid request.
 invalid_dialogs.insert(5);lock_fail=true;tick();lock_fail=false;
 assert(shell.show_message_dialog(0,6,options));assert(dialog->deleted);dialog=last_root();
 shell.hide_message_dialog(0,5);assert(!dialog->deleted);shell.hide_message_dialog(0,6);
 // Dialog clock pauses on display off, including an update received asleep.
 now=40000;options.auto_close_ms=10;assert(shell.show_message_dialog(0,7,options));dialog=last_root();
 display=false;assert(shell.set_display_on(false));now=90000;tick();assert(!dialog->deleted);
 assert(shell.update_message_dialog(0,7,options));dialog=last_root();now=190000;
 display=true;assert(shell.set_display_on(true));now=199999;tick();assert(!dialog->deleted);
 now=200000;tick();assert(dialog->deleted && dialogs.size()==4);
 // Quick Settings failures don't commit a different return Surface or base page.
 routing_fail=true;assert(!shell.show_surface(ShellSurface::QuickSettings));routing_fail=false;
 context.g.fail=true;assert(!shell.show_surface(ShellSurface::QuickSettings));assert(!shell.quick_settings_open());
 context.g.fail=false;assert(shell.show_surface(ShellSurface::QuickSettings));context.g.fail=true;
 assert(!shell.dismiss_quick_settings() && shell.quick_settings_open());context.g.fail=false;
 assert(shell.show_surface(ShellSurface::WatchFace));assert(!shell.quick_settings_open() && drop==1);
 // Loading tracks startup and explicit wait independently, with retry on failure.
 assert(shell.show_loading(8,true));auto* loading=last_root();assert(shell.show_loading(8));
 assert(!shell.show_loading(9));shell.hide_loading(8,true);assert(!loading->deleted);
 lock_fail=true;shell.hide_loading(8);tick();assert(!loading->deleted);
 lock_fail=false;tick();assert(loading->deleted);shell.hide_loading(8);tick();
 // No lower overlay is left accepting input after teardown of its request.
 assert(shell.show_keyboard(8,14,input));keyboard=last_root();assert(shell.cancel_keyboard_input());tick();
 assert(keys.size()==2 && !std::get<2>(keys.back()) && std::get<3>(keys.back()).empty());
 assert(!shell.cancel_keyboard_input());
 // Stable keyboard does not take the GUI lock on every maintenance tick.
 assert(shell.show_keyboard(8,15,input));keyboard=last_root();
 const auto stable_locks=lock_calls;for(int i=0;i<5;++i)tick();assert(lock_calls==stable_locks);
 // Real on_stop revokes callback state even when GUI deletion must be retried.
 options.auto_close_ms=0;assert(shell.show_message_dialog(0,9,options));dialog=last_root();
 assert(shell.show_loading(8));loading=last_root();lock_fail=true;
 assert(!shell.on_stop(context));ready(keyboard->children[2]);click(button(dialog));
 assert(keys.size()==2 && dialogs.size()==4 && !dialog->deleted);
 lock_fail=false;assert(shell.on_stop(context));assert(keyboard->deleted && dialog->deleted && loading->deleted);
 assert(keys.size()==2 && dialogs.size()==4);
 assert(shell.on_start(context));
 options.buttons.resize(4);assert(!shell.show_message_dialog(0,8,options));
 options.buttons.clear();options.auto_close_ms=-1;assert(!shell.show_message_dialog(0,8,options));
}
