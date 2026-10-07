"""Cancel real scheduler timer methods at the expiry/wait boundary."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/firmware'))
from prepare_patched_component import prepare

SOURCE = ROOT / 'firmware/managed_components/espressif__brookesia_lib_utils'
MANIFEST = ROOT / 'firmware/patches/espressif__brookesia_lib_utils/0.8.2/manifest.json'


def exercise(source, directory):
    text = (source / 'src/task_scheduler.cpp').read_text()
    methods = text[text.index('void TaskScheduler::Impl::schedule_once('):
                   text.index('bool TaskScheduler::Impl::suspend_internal(')]
    remove = text[text.index('void TaskScheduler::Impl::remove_task_internal('):
                  text.index('void TaskScheduler::Impl::mark_finished(')]
    code = r'''
#include <atomic>
#include <cassert>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <future>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#define BROOKESIA_LOG_TRACE_GUARD_WITH_THIS() ((void)0)
#define BROOKESIA_LOGD(...) ((void)0)
#define BROOKESIA_LOGW(...) ((void)0)
#define BROOKESIA_CHECK_EXCEPTION_EXECUTE(code, recovery, logging) try { code; } catch (...) { recovery; }
namespace boost {
using mutex = std::mutex;
using recursive_mutex = std::recursive_mutex;
template<class Mutex> using lock_guard = std::lock_guard<Mutex>;
namespace system {
struct error_code { bool failed = false; explicit operator bool() const { return failed; }
    bool operator==(const error_code &) const = default; };
}
namespace asio { namespace error { constexpr system::error_code operation_aborted{true}; } }
}
namespace esp_brookesia::lib_utils {
struct FunctionGuard {
    std::function<void()> callback;
    explicit FunctionGuard(std::function<void()> input) : callback(std::move(input)) {}
    ~FunctionGuard() { callback(); }
};
using TaskId = unsigned;
using Group = std::string;
enum class TaskState { Running, Suspended, Canceled, Finished };
enum class TaskType { Delayed, Periodic };
struct Boundary {
    std::mutex mutex;
    std::condition_variable cv;
    bool entered = false, requested = false, canceled = false;
};
struct Timer {
    Boundary *boundary;
    std::function<void(const boost::system::error_code &)> callback;
    void expires_after(std::chrono::milliseconds) {
        std::unique_lock lock(boundary->mutex);
        boundary->entered = true;
        boundary->cv.notify_all();
        boundary->cv.wait(lock, [&] { return boundary->requested; });
        boundary->cv.wait_for(lock, std::chrono::milliseconds(30), [&] { return boundary->canceled; });
    }
    void async_wait(std::function<void(const boost::system::error_code &)> input) { callback = std::move(input); }
    void cancel() {}
};
struct CheckedTimer {
    std::shared_ptr<Timer> timer;
    explicit operator bool() const { return bool(timer); }
    Timer *operator->() const {
        if (!timer) throw std::runtime_error("timer released between expiry and async_wait");
        return timer.get();
    }
    void reset() { timer.reset(); }
};
struct TaskScheduler {
    struct Impl {
        using OnceTask = std::function<void()>;
        using PeriodicTask = std::function<bool()>;
        struct TaskHandle {
            TaskId id = 1;
            Group group = "audio";
            TaskType type = TaskType::Periodic;
            bool repeat = true;
            int interval_ms = 1;
            std::atomic<TaskState> state{TaskState::Running};
            std::atomic<bool> is_executing{false};
            boost::recursive_mutex timer_mutex;
            CheckedTimer timer;
            std::shared_ptr<std::promise<bool>> promise;
        };
        boost::mutex mutex_;
        std::map<TaskId, std::shared_ptr<TaskHandle>> tasks_;
        std::map<Group, std::set<TaskId>> groups_;
        unsigned canceled_tasks_ = 0;
        void invoke_pre_execute_callback(TaskId, TaskType, const Group &) {}
        void invoke_post_execute_callback(TaskId, TaskType, bool, const Group &) {}
        void mark_finished(std::shared_ptr<TaskHandle> handle, bool) {
            handle->state = TaskState::Finished;
            boost::lock_guard<boost::mutex> lock(mutex_);
            remove_task_internal(handle->id, handle->group);
        }
        void schedule_once(std::shared_ptr<TaskHandle>, OnceTask);
        void schedule_periodic(std::shared_ptr<TaskHandle>, PeriodicTask);
        void cancel_internal(TaskId);
        void remove_task_internal(TaskId, const Group &);
    };
};
''' + methods + remove + r'''
}
int main() {
    using namespace esp_brookesia::lib_utils;
    for (bool periodic : {true, false}) {
        for (unsigned cycle = 0; cycle < 8; ++cycle) {
            Boundary boundary;
            TaskScheduler::Impl scheduler;
            auto handle = std::make_shared<TaskScheduler::Impl::TaskHandle>();
            auto timer = std::make_shared<Timer>();
            timer->boundary = &boundary;
            handle->timer.timer = timer;
            scheduler.tasks_[handle->id] = handle;
            scheduler.groups_[handle->group].insert(handle->id);
            unsigned invoked = 0;
            std::exception_ptr error;
            std::thread scheduling([&] {
                try {
                    if (periodic) scheduler.schedule_periodic(handle, [&] { ++invoked; return true; });
                    else scheduler.schedule_once(handle, [&] { ++invoked; });
                } catch (...) { error = std::current_exception(); }
            });
            {
                std::unique_lock lock(boundary.mutex);
                boundary.cv.wait(lock, [&] { return boundary.entered; });
            }
            std::thread canceling([&] {
                {
                    std::lock_guard lock(boundary.mutex);
                    boundary.requested = true;
                    boundary.cv.notify_all();
                }
                {
                    boost::lock_guard<boost::mutex> lock(scheduler.mutex_);
                    scheduler.cancel_internal(handle->id);
                }
                std::lock_guard lock(boundary.mutex);
                boundary.canceled = true;
                boundary.cv.notify_all();
            });
            scheduling.join();
            canceling.join();
            if (error) std::rethrow_exception(error);
            assert(handle->state == TaskState::Canceled && !handle->timer);
            assert(timer->callback);
            timer->callback(boost::asio::error::operation_aborted);
            assert(invoked == 0 && scheduler.tasks_.empty() && scheduler.groups_.empty());
            if (periodic) scheduler.schedule_periodic(handle, [&] { ++invoked; return true; });
            else scheduler.schedule_once(handle, [&] { ++invoked; });
            assert(invoked == 0 && !handle->timer);
        }
    }
}
'''
    cpp = Path(directory) / 'lifetime.cpp'
    binary = Path(directory) / 'lifetime'
    cpp.write_text(code)
    subprocess.run([os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread',
                    str(cpp), '-o', str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True, timeout=15)


class SchedulerTimerLifetimeTest(unittest.TestCase):
    def test_cancel_cannot_release_a_timer_during_scheduling(self):
        with tempfile.TemporaryDirectory(prefix='espocket-timer-lifetime-') as directory:
            self.assertNotEqual(exercise(SOURCE, directory).returncode, 0)
            patched = prepare(SOURCE, MANIFEST, Path(directory) / 'patched')
            result = exercise(patched, directory)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
