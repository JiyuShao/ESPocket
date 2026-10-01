#include "espocket/interaction_test_adapter.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>

#include "boost/json.hpp"
#include "driver/usb_serial_jtag.h"
#include "esp_app_desc.h"
#include "esp_err.h"
#include "esp_log.h"

namespace espocket {
namespace {

constexpr char TAG[] = "ESPocket.Test";
constexpr std::string_view FRAME_PREFIX = "@ESPTEST ";
constexpr size_t MAX_LINE_SIZE = 1024;

std::optional<uint64_t> unsigned_field(const boost::json::object &object, std::string_view key)
{
    const auto *value = object.if_contains(key);
    if (value == nullptr) {
        return std::nullopt;
    }
    if (value->is_uint64()) {
        return value->as_uint64();
    }
    if (value->is_int64() && value->as_int64() >= 0) {
        return static_cast<uint64_t>(value->as_int64());
    }
    return std::nullopt;
}

} // namespace

struct InteractionTestAdapter::ModeRequest {
    enum class State : uint8_t { Pending, Started, Cancelled, Done };

    explicit ModeRequest(bool requested_enabled) : enabled(requested_enabled)
    {
        completed = xSemaphoreCreateBinary();
    }

    ~ModeRequest()
    {
        if (completed != nullptr) {
            vSemaphoreDelete(completed);
        }
    }

    bool enabled;
    SemaphoreHandle_t completed = nullptr;
    std::expected<void, std::string> result;
    std::atomic<State> state = State::Pending;
};

InteractionTestAdapter::InteractionTestAdapter(std::shared_ptr<DeveloperMode> mode,
                                             TestProtocol::SnapshotReader snapshot_reader)
    : mode_(std::move(mode)), snapshot_reader_(std::move(snapshot_reader))
{}

InteractionTestAdapter::~InteractionTestAdapter()
{
    stop();
}

std::expected<void, std::string> InteractionTestAdapter::start()
{
    if (running_.load(std::memory_order_acquire)) {
        return {};
    }
    if (!mode_) {
        return std::unexpected("Developer mode control is unavailable");
    }
    if (usb_serial_jtag_is_driver_installed()) {
        return std::unexpected("USB Serial/JTAG is already owned by another input reader");
    }
    stopped_ = xSemaphoreCreateBinary();
    if (stopped_ == nullptr) {
        return std::unexpected("USB test stop semaphore allocation failed");
    }
    std::array<char, 65> image_sha{};
    esp_app_get_elf_sha256(image_sha.data(), image_sha.size());
    protocol_ = std::make_unique<TestProtocol>(*mode_, std::string(image_sha.data()), snapshot_reader_);
    running_.store(true, std::memory_order_release);
    driver_ready_.store(false, std::memory_order_release);
    const auto created = xTaskCreate(task_entry, "espocket_test_usb", 4096, this, 3, &task_);
    if (created != pdPASS) {
        running_.store(false, std::memory_order_release);
        protocol_.reset();
        vSemaphoreDelete(stopped_);
        stopped_ = nullptr;
        return std::unexpected("USB test task creation failed");
    }
    usb_serial_jtag_driver_config_t config = {
        .tx_buffer_size = 512,
        .rx_buffer_size = 512,
    };
    const auto installed = usb_serial_jtag_driver_install(&config);
    if (installed != ESP_OK) {
        ESP_LOGW(TAG, "USB transport unavailable; device developer-mode control remains active");
        return std::unexpected(std::string("USB test driver install failed: ") +
                               esp_err_to_name(installed));
    }
    driver_owned_ = true;
    driver_ready_.store(true, std::memory_order_release);
    ESP_LOGI(TAG, "USB Test Adapter ready; developer mode %s",
             mode_->enabled() ? "enabled" : "disabled");
    return {};
}

void InteractionTestAdapter::stop()
{
    if (!running_.exchange(false, std::memory_order_acq_rel)) {
        return;
    }
    driver_ready_.store(false, std::memory_order_release);
    if (stopped_ != nullptr && xSemaphoreTake(stopped_, pdMS_TO_TICKS(1000)) != pdTRUE) {
        ESP_LOGW(TAG, "USB Test Adapter task is still stopping");
        xSemaphoreTake(stopped_, portMAX_DELAY);
    }
    std::shared_ptr<ModeRequest> pending_request;
    {
        std::lock_guard lock(mode_request_mutex_);
        pending_request.swap(pending_mode_request_);
    }
    if (pending_request) {
        pending_request->state.store(ModeRequest::State::Cancelled, std::memory_order_release);
        pending_request->result = std::unexpected("Developer mode worker stopped");
        xSemaphoreGive(pending_request->completed);
    }
    task_ = nullptr;
    protocol_.reset();
    if (stopped_ != nullptr) {
        vSemaphoreDelete(stopped_);
        stopped_ = nullptr;
    }
    if (driver_owned_) {
        usb_serial_jtag_driver_uninstall();
        driver_owned_ = false;
    }
}

std::expected<void, std::string> InteractionTestAdapter::set_developer_mode(bool enabled)
{
    if (!running_.load(std::memory_order_acquire)) {
        return std::unexpected("Developer mode worker is unavailable");
    }
    auto request = std::make_shared<ModeRequest>(enabled);
    if (request->completed == nullptr) {
        return std::unexpected("Developer mode request allocation failed");
    }
    {
        std::lock_guard lock(mode_request_mutex_);
        if (pending_mode_request_) {
            return std::unexpected("Developer mode request is busy");
        }
        pending_mode_request_ = request;
    }
    if (xSemaphoreTake(request->completed, pdMS_TO_TICKS(5000)) != pdTRUE) {
        auto pending = ModeRequest::State::Pending;
        if (request->state.compare_exchange_strong(pending, ModeRequest::State::Cancelled)) {
            return std::unexpected("Developer mode storage timed out before it started");
        }
        // An NVS write already started; wait for its real result instead of
        // reporting a timeout while the gate could still change.
        xSemaphoreTake(request->completed, portMAX_DELAY);
    }
    return request->result;
}

void InteractionTestAdapter::task_entry(void *context)
{
    auto *self = static_cast<InteractionTestAdapter *>(context);
    self->run();
    xSemaphoreGive(self->stopped_);
    vTaskDelete(nullptr);
}

void InteractionTestAdapter::run()
{
    std::string line;
    line.reserve(256);
    std::array<uint8_t, 256> buffer{};
    bool discarding_oversized_line = false;
    while (running_.load(std::memory_order_acquire)) {
        std::shared_ptr<ModeRequest> mode_request;
        {
            std::lock_guard lock(mode_request_mutex_);
            mode_request.swap(pending_mode_request_);
        }
        if (mode_request) {
            auto pending = ModeRequest::State::Pending;
            if (mode_request->state.compare_exchange_strong(pending, ModeRequest::State::Started)) {
                mode_request->result = mode_->set_enabled(mode_request->enabled);
            }
            mode_request->state.store(ModeRequest::State::Done, std::memory_order_release);
            xSemaphoreGive(mode_request->completed);
        }
        if (!driver_ready_.load(std::memory_order_acquire)) {
            vTaskDelay(pdMS_TO_TICKS(20));
            continue;
        }
        const int count = usb_serial_jtag_read_bytes(buffer.data(), buffer.size(), pdMS_TO_TICKS(20));
        for (int i = 0; i < count; ++i) {
            const char ch = static_cast<char>(buffer[static_cast<size_t>(i)]);
            if (ch == '\n') {
                if (discarding_oversized_line) {
                    discarding_oversized_line = false;
                    line.clear();
                    continue;
                }
                if (!line.empty() && line.back() == '\r') {
                    line.pop_back();
                }
                handle_line(line);
                line.clear();
            } else if (discarding_oversized_line) {
                continue;
            } else if (line.size() < MAX_LINE_SIZE) {
                line.push_back(ch);
            } else {
                line.clear();
                discarding_oversized_line = true;
                send_error(0, "bad_request");
            }
        }
    }
}

void InteractionTestAdapter::handle_line(std::string_view line)
{
    if (!line.starts_with(FRAME_PREFIX)) {
        return;
    }
    boost::system::error_code error;
    auto request = boost::json::parse(line.substr(FRAME_PREFIX.size()), error);
    if (error || !request.is_object()) {
        send_error(0, "bad_request");
        return;
    }
    const auto &object = request.as_object();
    const auto request_id = unsigned_field(object, "request_id");
    const auto version = unsigned_field(object, "version");
    const auto *op = object.if_contains("op");
    if (!request_id || !version || *version > UINT32_MAX || op == nullptr || !op->is_string()) {
        send_error(request_id.value_or(0), "bad_request");
        return;
    }
    const auto &operation = op->as_string();
    const auto reply = protocol_->dispatch(static_cast<uint32_t>(*version),
                                           std::string_view(operation.data(), operation.size()));
    boost::json::object response = {
        {"version", TestProtocol::VERSION},
        {"request_id", *request_id},
        {"ok", reply.ok},
    };
    if (reply.ok) {
        if (reply.snapshot) {
            const auto &state = *reply.snapshot;
            response["snapshot"] = boost::json::object{
                {"seq", state.seq}, {"surface", state.surface}, {"display", state.display},
                {"foregroundAppId", state.foreground_app_id}, {"pageId", state.page_id},
                {"canBack", state.can_back}, {"backPending", state.back_pending},
            };
        } else {
            response["image_identity"] = reply.image_identity;
            boost::json::array capabilities;
            for (const auto &capability : reply.capabilities) {
                capabilities.emplace_back(capability);
            }
            response["capabilities"] = std::move(capabilities);
        }
    } else {
        response["error_code"] = reply.error_code;
    }
    send_line(std::string(FRAME_PREFIX) + boost::json::serialize(response) + "\n");
}

void InteractionTestAdapter::send_error(uint64_t request_id, std::string_view code)
{
    boost::json::object response = {
        {"version", TestProtocol::VERSION},
        {"request_id", request_id},
        {"ok", false},
        {"error_code", code},
    };
    send_line(std::string(FRAME_PREFIX) + boost::json::serialize(response) + "\n");
}

void InteractionTestAdapter::send_line(std::string_view line)
{
    size_t written = 0;
    while (written < line.size() && running_.load(std::memory_order_acquire)) {
        const int count = usb_serial_jtag_write_bytes(
            line.data() + written, line.size() - written, pdMS_TO_TICKS(100)
        );
        if (count <= 0) {
            ESP_LOGW(TAG, "USB Test Adapter response write failed");
            return;
        }
        written += static_cast<size_t>(count);
    }
}

} // namespace espocket
