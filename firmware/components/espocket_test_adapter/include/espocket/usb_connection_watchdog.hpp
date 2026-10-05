#pragma once
#include <cstdint>

namespace espocket {
// ESP-IDF's SOF monitor can report a missed short SOF window during a busy
// render. Require a sustained 200 ms loss before cancelling a live session.
// Input and screenshot lifetimes remain bounded independently.
class UsbConnectionWatchdog {
public:
    bool observe(bool raw_connected, uint64_t now_ms)
    {
        if (raw_connected) {
            connected_ = true;
            loss_pending_ = false;
        } else if (connected_) {
            if (!loss_pending_) { loss_pending_ = true; loss_at_ms_ = now_ms; }
            if (now_ms - loss_at_ms_ >= 200) connected_ = false;
        }
        return connected_;
    }
private:
    bool connected_ = false;
    bool loss_pending_ = false;
    uint64_t loss_at_ms_ = 0;
};
}
