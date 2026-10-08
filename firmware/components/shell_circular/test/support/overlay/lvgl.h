#pragma once

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
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
constexpr int LV_EVENT_DELETE=99,LV_EVENT_CLICKED=0;
#define LV_SYMBOL_DOWN "down"
struct lv_event_t {void* data;void* target=nullptr;void* current=nullptr;int code=0;};
struct lv_obj_t {void(*destroy)(lv_event_t*)=nullptr;void* destroy_data=nullptr;std::vector<lv_obj_t*> children;bool deleted=false;bool hidden=false;void(*click)(lv_event_t*)=nullptr;void* data=nullptr;std::string text;int width=0,height=0,bg_opa=-1,max_height=0;};
inline std::vector<std::unique_ptr<lv_obj_t>> allocated;
inline int fail_after=-1,lock_depth=0,lock_calls=0;inline bool lock_fail=false;inline int64_t now=0;
inline int64_t esp_timer_get_time() {return now;}
constexpr int LV_OBJ_FLAG_HIDDEN=1,LV_INDEV_TYPE_POINTER=1,LV_OBJ_FLAG_CLICKABLE=2,LV_ALIGN_BOTTOM_MID=3;
inline int lv_font_montserrat_20=0;
inline void lv_obj_add_flag(lv_obj_t* o,int flag){if(flag==LV_OBJ_FLAG_HIDDEN)o->hidden=true;}
inline void lv_obj_remove_flag(lv_obj_t* o,int flag){if(flag==LV_OBJ_FLAG_HIDDEN)o->hidden=false;}
inline bool lv_obj_is_valid(lv_obj_t* o){return o && !o->deleted;}
struct lv_indev_t {};
inline lv_indev_t* lv_indev_get_next(lv_indev_t*){return nullptr;}
inline int lv_indev_get_type(lv_indev_t*){return LV_INDEV_TYPE_POINTER;}
inline void lv_indev_enable(lv_indev_t*,bool){}

inline lv_obj_t layer;
inline lv_obj_t* lv_layer_top(){return &layer;}
inline lv_obj_t* lv_obj_create(lv_obj_t* parent){if(fail_after==0)return nullptr;if(fail_after>0)--fail_after;
    allocated.push_back(std::make_unique<lv_obj_t>());auto* o=allocated.back().get();parent->children.push_back(o);return o;}
inline auto lv_label_create=lv_obj_create;inline auto lv_button_create=lv_obj_create;inline auto lv_spinner_create=lv_obj_create;
inline void lv_obj_delete(lv_obj_t* o){assert(!o->deleted);o->deleted=true;for(auto* child:o->children)lv_obj_delete(child);if(o->destroy){lv_event_t e{o->destroy_data,o,o,LV_EVENT_DELETE};o->destroy(&e);}}
inline void lv_label_set_text(lv_obj_t* o,const char* text){o->text=text;}
inline void* lv_event_get_user_data(lv_event_t* e){return e->data;}
inline void* lv_event_get_target(lv_event_t* e){return e->target;}
inline void* lv_event_get_current_target(lv_event_t* e){return e->current;}

inline void lv_obj_add_event_cb(lv_obj_t* o,void(*cb)(lv_event_t*),int code,void* data){if(code==LV_EVENT_DELETE){o->destroy=cb;o->destroy_data=data;}else{o->click=cb;o->data=data;}}
inline void click(lv_obj_t* o){assert(!o->deleted && o->click);lv_event_t e{o->data,o,o,LV_EVENT_CLICKED};o->click(&e);}
inline int lv_pct(int n){return n;}inline int lv_color_hex(int n){return n;}inline int lv_font_montserrat_18=0;
constexpr int LV_OBJ_FLAG_SCROLLABLE=0,LV_OPA_80=0,LV_OPA_COVER=255,LV_OPA_TRANSP=0,LV_SIZE_CONTENT=-1,
    LV_FLEX_FLOW_COLUMN=0,LV_FLEX_FLOW_ROW=1,LV_FLEX_ALIGN_CENTER=0,LV_RADIUS_CIRCLE=100,
    LV_PART_MAIN=0,LV_PART_INDICATOR=1,LV_LABEL_LONG_MODE_WRAP=0,LV_LABEL_LONG_MODE_DOTS=0,LV_TEXT_ALIGN_CENTER=0,LV_STATE_PRESSED=1;

inline void lv_obj_set_size(lv_obj_t* o,int w,int h){o->width=w;o->height=h;}
inline int lv_obj_get_height(lv_obj_t* o){return o->height;}
inline void lv_obj_set_height(lv_obj_t* o,int h){o->height=h;}
inline void lv_obj_set_style_max_height(lv_obj_t* o,int h,int){o->max_height=h;}
inline void lv_obj_set_style_bg_opa(lv_obj_t* o,int opacity,int){o->bg_opa=opacity;}
template<class... T> void lv_obj_align(T...) {}
template<class... T> void lv_obj_move_to_index(T...) {}
template<class... T> void lv_obj_center(T...) {}
template<class... T> void lv_obj_set_style_bg_color(T...) {}
template<class... T> void lv_obj_set_style_border_width(T...) {}
template<class... T> void lv_obj_set_style_radius(T...) {}
template<class... T> void lv_obj_set_style_pad_all(T...) {}
template<class... T> void lv_obj_set_style_pad_row(T...) {}
template<class... T> void lv_obj_set_flex_flow(T...) {}
template<class... T> void lv_obj_set_width(T...) {}
template<class... T> void lv_obj_set_flex_grow(T...) {}
template<class... T> void lv_label_set_long_mode(T...) {}
template<class... T> void lv_obj_set_style_text_color(T...) {}
template<class... T> void lv_obj_set_style_text_font(T...) {}
template<class... T> void lv_obj_set_style_text_align(T...) {}
template<class... T> void lv_obj_set_style_border_color(T...) {}
template<class... T> void lv_obj_set_style_pad_column(T...) {}
template<class... T> void lv_obj_set_flex_align(T...) {}
template<class... T> void lv_spinner_set_anim_params(T...) {}
template<class... T> void lv_obj_set_style_arc_width(T...) {}
template<class... T> void lv_obj_set_style_arc_color(T...) {}
template<class... T> void lv_obj_add_state(T...) {}
template<class... T> void lv_textarea_set_one_line(T...) {}
template<class... T> void lv_textarea_set_password_mode(T...) {}
template<class... T> void lv_textarea_set_password_show_time(T...) {}
template<class... T> void lv_textarea_set_max_length(T...) {}
template<class... T> void lv_textarea_set_placeholder_text(T...) {}
template<class... T> void lv_keyboard_set_textarea(T...) {}
template<class... T> void lv_keyboard_set_mode(T...) {}
template<class... T> void lv_keyboard_set_popovers(T...) {}

using lv_keyboard_mode_t=int;using lv_style_selector_t=uint32_t;
constexpr int LV_KEYBOARD_MODE_NUMBER=0,LV_KEYBOARD_MODE_SPECIAL=1,LV_KEYBOARD_MODE_TEXT_UPPER=2,LV_KEYBOARD_MODE_TEXT_LOWER=3;
constexpr int LV_ALIGN_TOP_MID=4,LV_PART_TEXTAREA_PLACEHOLDER=5,LV_PART_ITEMS=6,LV_STATE_FOCUSED=7,LV_EVENT_READY=8,LV_EVENT_CANCEL=9;
inline auto lv_textarea_create=lv_obj_create;inline auto lv_keyboard_create=lv_obj_create;
inline void lv_textarea_set_text(lv_obj_t* o,const char* text){o->text=text;}
inline const char* lv_textarea_get_text(lv_obj_t* o){return o->text.c_str();}
inline int lv_event_get_code(lv_event_t* e){return e->code;}
inline void lv_indev_wait_release(lv_indev_t*){}
inline void ready(lv_obj_t* o,int code=LV_EVENT_READY){assert(o->click);lv_event_t e{o->data,o,o,code};o->click(&e);}
inline int esp_lv_adapter_lock(int){++lock_calls;if(lock_fail)return -1;++lock_depth;return 0;}
inline void esp_lv_adapter_unlock(){--lock_depth;}
constexpr int ESP_OK=0;

struct lv_point_t {int32_t x=0,y=0;};
struct lv_indev_data_t {int state=0;lv_point_t point;};
using lv_indev_read_cb_t=void(*)(lv_indev_t*,lv_indev_data_t*);
struct lv_event_dsc_t {};
constexpr int LV_EVENT_ALL=100,LV_EVENT_SHORT_CLICKED=101,LV_INDEV_STATE_RELEASED=0,LV_INDEV_STATE_PRESSED=1;
inline lv_indev_read_cb_t lv_indev_get_read_cb(lv_indev_t*){return nullptr;}
inline uint32_t lv_indev_get_event_count(lv_indev_t*){return 0;}
template<class... T> void lv_indev_add_event_cb(T...){}
template<class... T> void lv_indev_set_read_cb(T...){}
template<class... T> void lv_indev_remove_event_cb_with_user_data(T...){}
inline void lv_indev_stop_processing(lv_indev_t*){}
inline lv_event_dsc_t* lv_indev_get_event_dsc(lv_indev_t*,uint32_t){return nullptr;}
inline void(*lv_event_dsc_get_cb(lv_event_dsc_t*))(lv_event_t*){return nullptr;}
inline void* lv_event_dsc_get_user_data(lv_event_dsc_t*){return nullptr;}
