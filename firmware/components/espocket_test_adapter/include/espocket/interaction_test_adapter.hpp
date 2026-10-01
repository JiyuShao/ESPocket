#pragma once

#include <atomic>
#include <expected>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

#include "espocket/developer_mode.hpp"
#include "espocket/test_protocol.hpp"

namespace espocket {

class InteractionTestAdapter {
public:
    explicit InteractionTestAdapter(std::shared_ptr<DeveloperMode> mode,
                                    TestProtocol::SnapshotReader snapshot_reader = {});
    ~InteractionTestAdapter();

    std::expected<void, std::string> start();
    std::expected<void, std::string> set_developer_mode(bool enabled);
    void stop();

private:
    struct ModeRequest;
    static void task_entry(void *context);
    void run();
    void handle_line(std::string_view line);
    void send_error(uint64_t request_id, std::string_view code);
    void send_line(std::string_view line);

    std::shared_ptr<DeveloperMode> mode_;
    std::unique_ptr<TestProtocol> protocol_;
    TestProtocol::SnapshotReader snapshot_reader_;
    std::atomic_bool running_ = false;
    std::atomic_bool driver_ready_ = false;
    std::mutex mode_request_mutex_;
    std::shared_ptr<ModeRequest> pending_mode_request_;
    TaskHandle_t task_ = nullptr;
    SemaphoreHandle_t stopped_ = nullptr;
    bool driver_owned_ = false;
};

} // namespace espocket
