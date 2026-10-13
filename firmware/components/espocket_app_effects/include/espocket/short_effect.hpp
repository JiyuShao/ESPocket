#pragma once
#include <atomic>
#include "brookesia/service_audio/service_audio.hpp"
#include "brookesia/service_manager/service/manager.hpp"
namespace espocket {
// One short PCM stream through the existing Audio Owner. Busy output is skipped.
class ShortEffect {
public:
    explicit ShortEffect(std::string source_name) : source_name_(std::move(source_name)) {}
    ~ShortEffect() { close(); }
    void play(unsigned hz, unsigned ms);
    void poll();
    void close();
private:
    std::string source_name_;
    esp_brookesia::service::ServiceBinding binding_;
    std::optional<uint32_t> source_;
    std::string output_;
    std::shared_ptr<std::atomic<int64_t>> released_at_us_;
    int64_t duration_us_ = 0;
};
}
