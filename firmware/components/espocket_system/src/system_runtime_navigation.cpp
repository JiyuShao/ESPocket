#include "system_internal.hpp"
#include "runtime_navigation_provider.hpp"
#include "espocket/navigation_request_queue.hpp"
#include "espocket/runtime_page_adapter.hpp"
#include "brookesia/service_helper/system/storage.hpp"
#include <filesystem>

namespace espocket {
void System::init_runtime_navigation()
{
    if (runtime_requests_) runtime_requests_->close();
    runtime_requests_ = std::make_shared<NavigationRequestQueue>();
    RuntimeNavigationProvider::instance().bind([this, queue = runtime_requests_](
        const esp_brookesia::runtime::NativeArgs &arguments,
        esp_brookesia::runtime::NativeAsyncCallback reply) {
        if (arguments.size() != 1 || !std::holds_alternative<std::string>(arguments.front())) {
            reply(std::unexpected("bad_request")); return;
        }
        auto owner = get_current_runtime_app_owner();
        const auto generation = foreground_token_->load(std::memory_order_acquire);
        if (!owner || *owner != foreground_app_id_.load(std::memory_order_acquire)) {
            reply(std::unexpected("not_started")); return;
        }
        queue->enqueue(*owner, generation, static_cast<uint64_t>(esp_timer_get_time() / 1000),
            std::get<std::string>(arguments.front()), [reply = std::move(reply)](auto result) mutable {
                if (result) reply(esp_brookesia::runtime::NativeValue(std::move(*result)));
                else reply(std::unexpected(std::move(result.error())));
            });
    });
}

void System::stop_runtime_navigation()
{
    RuntimeNavigationProvider::instance().bind({});
    if (runtime_requests_) runtime_requests_->close();
}

std::shared_ptr<RuntimePageAdapter> System::runtime_adapter_for(
    esp_brookesia::system::core::AppId id) const
{
    std::lock_guard lock(page_navigators_mutex_);
    const auto found = runtime_pages_.find(id);
    return found == runtime_pages_.end() ? nullptr : found->second.adapter;
}

bool System::runtime_page_matches(esp_brookesia::system::core::AppId id) const
{
    std::string flow;
    std::shared_ptr<RuntimePageAdapter> adapter;
    {
        std::lock_guard lock(page_navigators_mutex_);
        const auto found = runtime_pages_.find(id);
        if (found == runtime_pages_.end()) return true;
        flow = found->second.flow;
        adapter = found->second.adapter;
    }
    const auto state = gui_get_screen_flow_state(id, flow);
    return state && *state == adapter->navigator()->snapshot().page_id;
}

std::expected<void, std::string> System::on_app_installed(
    const esp_brookesia::system::core::AppInfo &app)
{
    using namespace esp_brookesia::system::core;
    if (app.manifest.kind != AppKind::Runtime || !app.manifest.visible) return {};
    const auto path = std::filesystem::path(app.manifest.app_path) / app.manifest.resource_dir / "navigation.json";
    auto json = esp_brookesia::service::helper::Storage::fs_read_text(path.generic_string(), 5000);
    if (!json) return std::unexpected("Runtime navigation declaration missing: " + json.error());
    auto definition = decode_runtime_pages(*json);
    if (!definition) return std::unexpected(definition.error());
    if (definition->declaration.app_id != app.manifest.id) return std::unexpected("identity_mismatch");
    const auto flow = definition->screen_flow;
    const auto card_declaration = definition->declaration;
    auto adapter = RuntimePageAdapter::create(std::move(*definition),
        [this, id = app.app_id](auto flow, auto action, auto from, auto to) {
            const auto before = gui_get_screen_flow_state(id, flow);
            if (!before || *before != from) return false;
            if (!gui_trigger_screen_flow(id, flow, action)) return false;
            const auto after = gui_get_screen_flow_state(id, flow);
            return after && *after == to;
        });
    if (!adapter) return std::unexpected(adapter.error());
    if (!cards_ || !cards_->register_app(card_declaration)) return std::unexpected("card_declaration_registration_failed");
    register_navigator(app.app_id, (*adapter)->navigator());
    { std::lock_guard lock(page_navigators_mutex_); runtime_pages_.emplace(app.app_id, RuntimePages{*adapter, flow}); }
    return {};
}

void System::drain_runtime_navigation()
{
    if (!runtime_requests_) return;
    runtime_requests_->drain(foreground_app_id_.load(std::memory_order_acquire),
        foreground_token_->load(std::memory_order_acquire),
        static_cast<uint64_t>(esp_timer_get_time() / 1000),
        [this](uint32_t app, std::string_view request) -> NavigationRequestQueue::Result {
            auto adapter = runtime_adapter_for(app);
            if (!adapter) return std::unexpected("page_adapter_unavailable");
            if (!runtime_page_matches(app)) return std::unexpected("invalid_state");
            return adapter->dispatch(request, static_cast<uint64_t>(esp_timer_get_time() / 1000));
        });
    const auto app = foreground_app_id_.load(std::memory_order_acquire);
    if (runtime_adapter_for(app) && !runtime_page_matches(app)) {
        default_back_visible_.store(false, std::memory_order_release);
        edge_back_enabled_.store(false, std::memory_order_release);
    }
}
} // namespace espocket
