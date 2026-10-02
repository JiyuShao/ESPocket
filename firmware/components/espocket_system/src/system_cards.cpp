#include "system_internal.hpp"
#include "espocket/card_configuration_store.hpp"
#include "espocket/navigation_request_queue.hpp"
#include "card_document.hpp"
#include "nvs.h"

namespace espocket {
namespace {
constexpr char CARD_STORAGE_NAMESPACE[] = "espocket";
constexpr char CARD_STORAGE_KEY[] = "cards_v1";

std::expected<std::optional<std::string>, std::string> read_cards()
{
    nvs_handle_t handle;
    auto error = nvs_open(CARD_STORAGE_NAMESPACE, NVS_READONLY, &handle);
    if (error == ESP_ERR_NVS_NOT_FOUND) return std::optional<std::string>{};
    if (error != ESP_OK) return std::unexpected(esp_err_to_name(error));
    size_t size = 0;
    error = nvs_get_str(handle, CARD_STORAGE_KEY, nullptr, &size);
    if (error == ESP_ERR_NVS_NOT_FOUND) { nvs_close(handle); return std::optional<std::string>{}; }
    if (error != ESP_OK || size == 0 || size > 16'385) {
        nvs_close(handle); return std::unexpected("invalid_card_storage");
    }
    std::string json(size, '\0');
    error = nvs_get_str(handle, CARD_STORAGE_KEY, json.data(), &size);
    nvs_close(handle);
    if (error != ESP_OK) return std::unexpected(esp_err_to_name(error));
    json.resize(size - 1);
    return std::optional<std::string>(std::move(json));
}

std::expected<void, std::string> write_cards(std::string_view json)
{
    nvs_handle_t handle;
    auto error = nvs_open(CARD_STORAGE_NAMESPACE, NVS_READWRITE, &handle);
    if (error != ESP_OK) return std::unexpected(esp_err_to_name(error));
    const std::string terminated(json);
    error = nvs_set_str(handle, CARD_STORAGE_KEY, terminated.c_str());
    if (error == ESP_OK) error = nvs_commit(handle);
    nvs_close(handle);
    if (error != ESP_OK) return std::unexpected(esp_err_to_name(error));
    return {};
}
}

void System::init_cards()
{
    cards_ = std::make_unique<CardRegistry>();
    card_store_ = std::make_unique<CardConfigurationStore>(*cards_, read_cards, write_cards);
    card_actions_ = std::make_shared<NavigationRequestQueue>();
    card_session_ = std::make_unique<CardSession>(*cards_, [this](const CardKey &key) -> std::unique_ptr<CardContent> {
        const auto apps = list_apps();
        const auto app = std::ranges::find_if(apps, [&](const auto &candidate) { return candidate.manifest.id == key.app_id; });
        if (app == apps.end()) return nullptr;
        const auto factory = card_factories_.find(app->app_id);
        if (factory == card_factories_.end()) return nullptr;
        card_owner_id_ = app->app_id;
        return CardDocument::create(system_gui(), factory->second(key.card_id), [this, id = app->app_id] {
            const auto generation = card_generation_;
            auto queue = card_actions_;
            return [queue, id, generation](std::string action) {
                queue->enqueue(id, generation, static_cast<uint64_t>(esp_timer_get_time() / 1000), std::move(action),
                    [](auto result) { if (!result) ESP_LOGW(TAG, "Card action rejected: %s", result.error().c_str()); });
            };
        });
    });
    cards_->set_removal_handler([this](const CardRemoval &removal) {
        ESP_LOGI(TAG, "Card removed: app=%s card=%s reason=%d", removal.key.app_id.c_str(),
                 removal.key.card_id.c_str(), static_cast<int>(removal.reason));
        if (card_session_ && card_session_->key() == removal.key) {
            card_generation_ = 0;
            (void)card_session_->invalidate(removal.key);
        }
    });
}

std::expected<void, std::string> System::init_card_samples()
{
#if CONFIG_ESPOCKET_M8_CARD_SAMPLE_TEST
    if (!cards_ || !developer_mode_ || !developer_mode_->enabled()) return {};
    const auto current = cards_->configuration();
    if (!current.left.empty() || !current.right.empty()) {
        ESP_LOGI(TAG, "Card sample fixture skipped: existing configuration");
        return {};
    }
    CardConfiguration samples{
        .left = {{"espocket.app.hello", "summary"}, {"espocket.app.hello", "detail"}},
        .right = {{"espocket.app.hello_runtime", "summary"}, {"espocket.app.hello_runtime", "detail"}},
    };
    if (!cards_->replace_configuration(std::move(samples))) return std::unexpected("card_sample_declaration_unavailable");
    card_samples_active_ = true;
    ESP_LOGI(TAG, "CARD_SAMPLE_TEST temporary Native/Runtime configuration active; NVS unchanged");
#endif
    return {};
}

void System::pause_card()
{
    card_generation_ = 0;
    if (card_session_) (void)card_session_->pause();
}

std::expected<void, std::string> System::resume_card()
{
    if (!card_session_ || !card_session_->key() || !shell_) return {};
    const auto key = *card_session_->key();
    const auto configuration = cards_->configuration();
    const bool left = std::ranges::find(configuration.left, key) != configuration.left.end();
    const bool right = std::ranges::find(configuration.right, key) != configuration.right.end();
    if (!left && !right) return shell_->show_watch_face();
    pause_card();
    if (auto shown = shell_->show_surface(left ? ShellSurface::LeftAppCard : ShellSurface::RightAppCard); !shown) return shown;
    do { ++next_card_generation_; } while (next_card_generation_ == 0);
    card_generation_ = next_card_generation_;
    if (!card_session_->show(key)) {
        pause_card();
        (void)shell_->show_watch_face();
        return std::unexpected("card_presentation_failed");
    }
    return {};
}

void System::card_surface_changed(ShellSurface surface)
{
    if (surface != ShellSurface::LeftAppCard && surface != ShellSurface::RightAppCard) pause_card();
}

std::expected<void, std::string> System::step_card(bool left, bool inward)
{
    if (!cards_ || !card_session_ || !shell_) return std::unexpected("card_unavailable");
    if (foreground_token_->load() != 0 || !display_on_.load()) return std::unexpected("invalid_state");
    const auto configuration = cards_->configuration();
    const auto &sequence = left ? configuration.left : configuration.right;
    size_t index = 0;
    const auto surface = left ? ShellSurface::LeftAppCard : ShellSurface::RightAppCard;
    if (shell_->current_surface() == surface && card_session_->key()) {
        const auto found = std::ranges::find(sequence, *card_session_->key());
        if (found == sequence.end()) return shell_->show_watch_face();
        index = static_cast<size_t>(found - sequence.begin());
        if (inward && index == 0) return shell_->show_watch_face();
        if (inward) --index;
        else if (++index >= sequence.size()) return {};
    } else if (inward) return shell_->show_watch_face();
    if (sequence.empty()) return shell_->show_surface(left ? ShellSurface::BatteryCard : ShellSurface::BrightnessCard);
    pause_card();
    if (auto shown = shell_->show_surface(surface); !shown) return shown;
    do { ++next_card_generation_; } while (next_card_generation_ == 0);
    card_generation_ = next_card_generation_;
    const auto shown = card_session_->show(sequence[index]);
    if (!shown) {
        pause_card();
        (void)shell_->show_watch_face();
        return std::unexpected("card_presentation_failed");
    }
    return {};
}

void System::drain_card_actions()
{
    if (!card_actions_ || !card_session_) return;
    const auto generation = card_session_->visibility() == CardVisibility::Visible && display_on_.load() &&
        foreground_token_->load() == 0 ? card_generation_ : 0;
    card_actions_->drain(card_owner_id_, generation, static_cast<uint64_t>(esp_timer_get_time() / 1000),
        [this](uint32_t app, std::string_view action) -> NavigationRequestQueue::Result {
            if (app != card_owner_id_ || card_generation_ == 0 || foreground_token_->load() != 0 ||
                !display_on_.load() || card_session_->visibility() != CardVisibility::Visible) {
                return std::unexpected("stale_request");
            }
            if (action != CARD_OPEN_APP_ACTION) {
                if (!card_session_->action(action)) return std::unexpected("card_action_failed");
                return "done";
            }
            const auto opened = card_session_->open_app([this](const CardKey &key, std::string_view) {
                pending_card_ = key;
                const auto launched = launch_app(key.app_id, shell_->current_surface());
                pending_card_.reset();
                return launched.has_value();
            });
            card_generation_ = 0;
            if (!opened) {
                (void)shell_->show_watch_face();
                return std::unexpected("card_launch_failed");
            }
            return "done";
        });
    if (card_session_->key() && !cards_->target_page(*card_session_->key())) {
        card_generation_ = 0;
        (void)card_session_->release();
    }
    if (!card_session_->key() && shell_ && foreground_token_->load() == 0 &&
        (shell_->current_surface() == ShellSurface::LeftAppCard || shell_->current_surface() == ShellSurface::RightAppCard)) {
        (void)shell_->show_watch_face();
    }
}

std::expected<void, std::string> System::configure_cards(CardConfiguration configuration)
{
    if (!card_store_ || stopping_.load()) return std::unexpected("system_unavailable");
    if (card_session_ && card_session_->busy()) return std::unexpected("card_busy");
    const auto saved = card_store_->apply(std::move(configuration));
    if (!saved) return saved;
    card_samples_active_ = false; // Explicit user configuration replaces the temporary fixture.
    if (card_session_ && card_session_->visibility() == CardVisibility::Visible && shell_) {
        const auto key = card_session_->key();
        const auto committed = cards_->configuration();
        if (key) {
            const bool left = std::ranges::find(committed.left, *key) != committed.left.end();
            const auto desired = left ? ShellSurface::LeftAppCard : ShellSurface::RightAppCard;
            if (shell_->current_surface() != desired) return resume_card();
        }
    }
    return {};
}

CardConfiguration System::card_configuration() const
{
    return cards_ ? cards_->configuration() : CardConfiguration{};
}

std::vector<CardKey> System::available_cards() const
{
    return cards_ ? cards_->available_cards() : std::vector<CardKey>{};
}

std::expected<void, std::string> System::update_navigated_declaration(
    esp_brookesia::system::core::AppId id, PageDeclaration declaration)
{
    auto navigator = navigator_for(id);
    if (!navigator || !cards_) return std::unexpected("page_adapter_unavailable");
    if (card_session_ && card_session_->busy()) return std::unexpected("card_busy");
    if (runtime_adapter_for(id)) return std::unexpected("runtime_package_update_required");
    // Shared validation and stable identity are checked before changing either Owner.
    auto updated = navigator->update_declaration(declaration);
    if (!updated) return std::unexpected(std::string(navigation_error_name(updated.error())));
    if (!cards_->update_app(std::move(declaration))) return std::unexpected("card_declaration_update_failed");
    return card_samples_active_ ? std::expected<void, std::string>{} : card_store_->save_current();
}
}
