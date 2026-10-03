"""Exercise actual Display frame/backlight methods against one contended LCD IO sink."""
from pathlib import Path
import subprocess,tempfile,sys,unittest
ROOT = Path(__file__).resolve().parents[3]

def run_io_regression(source):
    source=Path(source)
    def method(file,signature):
     text=(source/file).read_text();start=text.index(signature);brace=text.index('{',start);level=1;i=brace+1
     while level:
      if text[i]=='{':level+=1
      if text[i]=='}':level-=1
      i+=1
     return text[start:i]
    methods='\n'.join([method('src/display_backlight.cpp','std::expected<void, std::string> Display::function_set_backlight_brightness('),method('src/display_backlight.cpp','std::expected<void, std::string> Display::function_set_backlight_on_off('),method('src/display_backlight.cpp','std::expected<void, std::string> Display::function_load_data('),method('src/display_backlight.cpp','std::expected<void, std::string> Display::function_reset_data('),method('src/display_output_source.cpp','Display::PresentResult Display::present_frame_sync(')])
    extra=''
    text=(source/'src/display_backlight.cpp').read_text()
    if 'Display::get_backlight_draw_mutex(' in text:extra=method('src/display_backlight.cpp','std::expected<std::shared_ptr<std::mutex>, std::string> Display::get_backlight_draw_mutex(')
    harness=r'''
    #include <atomic>
    #include <cassert>
    #include <chrono>
    #include <condition_variable>
    #include <expected>
    #include <future>
    #include <map>
    #include <memory>
    #include <mutex>
    #include <string>
    #include <thread>
    #include <vector>
    #include <tuple>
    #define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS(...) ((void)0)
    #define BROOKESIA_SERVICE_DISPLAY_BACKLIGHT_KV_ERASE_DATA_TIMEOUT_MS 500
    #define BROOKESIA_LOGW(...) ((void)0)
    namespace helper {struct Storage {static bool is_available(){return false;} static std::expected<void,std::string> erase_keys(std::string,std::vector<std::string>,int){return {};}};}
    const char *KEY_BRIGHTNESS="Brightness", *KEY_ON="On";
    #define BROOKESIA_LOGD(...) ((void)0)
    namespace boost {struct format {format(const char*){}template<class T>format& operator%(T){return *this;}std::string str(){return "error";}};}
    struct Probe {std::mutex mutex;std::condition_variable cv;bool drawing=false,release=false,control=false;std::atomic_bool overlap=false;
     void frame(){std::unique_lock lock(mutex);drawing=true;cv.notify_all();cv.wait(lock,[&]{return release;});drawing=false;}
     void backlight(){std::lock_guard lock(mutex);if(drawing)overlap=true;control=true;cv.notify_all();}};
    struct Info {uint32_t id=1;std::string name="lcd";};struct Panel {};struct Backlight {};
    struct FrameInfo {};struct RawBuffer {const void* data_ptr;size_t data_size;};
    struct Display {enum class PresentResult {Error,DroppedNotActive,DroppedInvalidFrame,Presented};
     struct OutputContext {Info info;std::shared_ptr<Panel> panel=std::make_shared<Panel>();std::shared_ptr<Backlight> backlight=std::make_shared<Backlight>();
     std::shared_ptr<std::mutex> draw_mutex=std::make_shared<std::mutex>();uint32_t active_source_id=1;uint8_t backlight_brightness=40;bool backlight_on=true;int buffer=0;};
     struct OutputDrawTarget {Info info;Panel* panel;int buffer;};
     std::mutex mutex_;std::map<uint32_t,int> sources_{{1,0}};std::map<uint32_t,OutputContext> outputs_{{1,OutputContext{}}};Probe probe;
     std::expected<uint32_t,std::string> validate_output_id_param(double id){return uint32_t(id);}
     std::expected<uint8_t,std::string> validate_percentage(double p,const char*){return uint8_t(p);}
     std::expected<uint32_t,std::string> find_output_id_locked(std::string_view){return 1;}
     std::string get_backlight_storage_output_id(const OutputContext&){return "lcd";}
     bool apply_backlight_state_to_hal(OutputContext&){probe.backlight();return true;}
     void save_backlight_brightness_data(std::string,uint8_t){}void emit_backlight_brightness_changed(uint32_t,std::string,uint8_t){}
     void save_backlight_on_off_data(std::string,bool){}void emit_backlight_on_off_changed(uint32_t,std::string,bool){}
     bool is_frame_valid_for_output(const FrameInfo&,const OutputContext&,size_t){return true;}
     PresentResult present_frame_to_output(const OutputDrawTarget&,const FrameInfo&,const RawBuffer&,uint32_t){probe.frame();return PresentResult::Presented;}
     void emit_frame_presented(std::string,const FrameInfo&){}
     std::expected<std::vector<uint32_t>,std::string> collect_backlight_output_ids_locked(uint32_t){return std::vector<uint32_t>{1};}
     std::expected<std::string,std::string> make_backlight_storage_namespace(){return "display";}
     std::expected<std::string,std::string> make_backlight_storage_key(std::string,const char*){return "key";}
     void load_backlight_data_from_storage_locked(OutputContext& output){output.backlight_brightness=70;}
     void reset_backlight_data_locked(OutputContext& output){output.backlight_brightness=30;apply_backlight_state_to_hal(output);}
     std::expected<void,std::string> function_load_data(double);std::expected<void,std::string> function_reset_data(double);
     std::expected<std::shared_ptr<std::mutex>,std::string> get_backlight_draw_mutex(uint32_t);
     std::expected<void,std::string> function_set_backlight_brightness(double,double);
     std::expected<void,std::string> function_set_backlight_on_off(double,bool);
     PresentResult present_frame_sync(uint32_t,std::string_view,const FrameInfo&,const RawBuffer&,uint32_t);
    };
    '''+extra+methods+('constexpr bool patched = true;\n' if extra else 'constexpr bool patched = false;\n')+r'''
    int main(){for(int operation:{0,1,2,3}){
     Display d;int pixel=0;auto drawing=std::async(std::launch::async,[&]{return d.present_frame_sync(1,"lcd",{},RawBuffer{&pixel,sizeof(pixel)},0);});
     {std::unique_lock lock(d.probe.mutex);assert(d.probe.cv.wait_for(lock,std::chrono::seconds(1),[&]{return d.probe.drawing;}));}
     auto setting=std::async(std::launch::async,[&]{switch(operation){case 0:return d.function_set_backlight_brightness(1,70);case 1:return d.function_set_backlight_on_off(1,false);case 2:return d.function_load_data(1);default:return d.function_reset_data(1);}});
     {std::unique_lock lock(d.probe.mutex);d.probe.cv.wait_for(lock,std::chrono::milliseconds(200),[&]{return d.probe.control;});if(patched){bool free=d.mutex_.try_lock();assert(free && "must not hold Display state while waiting for output IO");d.mutex_.unlock();}d.probe.release=true;d.probe.cv.notify_all();}
     assert(drawing.get()==Display::PresentResult::Presented);assert(setting.get());assert(!d.probe.overlap && "brightness/power must not overlap an in-progress frame on the same LCD IO");
     assert(!d.function_set_backlight_brightness(99,80));assert(!d.function_set_backlight_on_off(99,true));
    }}
    '''
    with tempfile.TemporaryDirectory(prefix='espocket-display-io-') as directory:
     cpp=Path(directory)/'test.cpp';binary=Path(directory)/'test';cpp.write_text(harness)
     subprocess.run(['clang++','-std=c++23','-pthread',str(cpp),'-o',str(binary)],check=True)
     subprocess.run([str(binary)],check=True,timeout=5,capture_output=True,text=True)

class DisplayIoSerializationTest(unittest.TestCase):
    def test_original_can_overlap_frame_and_backlight(self):
        with self.assertRaises(subprocess.CalledProcessError) as failure:
            run_io_regression(ROOT / 'firmware/managed_components/espressif__brookesia_service_display')
        self.assertIn('must not overlap an in-progress frame', failure.exception.stderr)

    def test_candidate_serializes_brightness_power_load_and_reset(self):
        sys.path.insert(0, str(ROOT / 'scripts/firmware'))
        from prepare_patched_component import prepare
        with tempfile.TemporaryDirectory(prefix='espocket-display-patched-') as directory:
            source = prepare(ROOT / 'firmware/managed_components/espressif__brookesia_service_display',
                             ROOT / 'firmware/patches/espressif__brookesia_service_display/0.8.2/manifest.json',
                             Path(directory) / 'display')
            run_io_regression(source)
