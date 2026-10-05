#include <array>
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include "espocket/test_protocol.hpp"

void require(bool ok, const char *message) {
    if (!ok) { std::cerr << message << '\n'; std::exit(1); }
}
int main() {
    std::array<uint8_t, 12> pixels{};
    std::array<uint8_t, 1> coverage{};
    espocket::ScreenshotAssembly assembly(3, 2, pixels, coverage);
    const std::array<uint8_t, 8> row{0, 248, 224, 7, 31, 0, 99, 99};
    require(assembly.append(0, 0, 2, 0, row, 8) && !assembly.complete(), "partial screen rejected");
    require(assembly.append(0, 0, 2, 0, row, 8) && !assembly.complete(), "duplicate rows don't cover missing pixels");
    require(assembly.append(0, 1, 2, 1, row, 8) && assembly.complete() && pixels[7] == 248 && pixels[11] == 0,
            "RGB565 rows assemble without padding or byte swap");
    require(!assembly.append(-1, 0, 0, 0, row, 8) && !assembly.complete(), "invalid region invalidates capture");
    espocket::ScreenshotAssembly truncated(3, 2, pixels, coverage);
    require(!truncated.append(0, 0, 2, 1, row, 8), "truncated source rejected before second row read");
    espocket::DeveloperMode mode([] { return std::expected<bool, std::string>(false); },
        [](bool) { return std::expected<void, std::string>{}; });
    uint64_t now = 100;
    int calls = 0;
    std::weak_ptr<uint8_t> retained;
    espocket::TestProtocol visual(mode, "visual-image", {}, {}, [] { return std::expected<void, std::string>{}; }, {},
        [&]() -> std::expected<espocket::TestScreenshot, std::string> {
            ++calls;
            auto bytes = std::shared_ptr<uint8_t>(new uint8_t[12]{0,248,224,7,31,0}, std::default_delete<uint8_t[]>());
            retained = bytes;
            return espocket::TestScreenshot{3, 2, 12, bytes, std::string(64, 'a')};
        }, [&] { return now; });
    require(visual.dispatch(1, "screenshot").error_code == "developer_mode_off" && calls == 0, "disabled capture cannot read pixels");
    require(mode.set_enabled(true).has_value(), "enable fixture");
    auto hello = visual.dispatch(1, "hello");
    require(std::ranges::find(hello.capabilities, "screenshot") != hello.capabilities.end(), "bound capability advertised");
    uint64_t id;
    { auto image = visual.dispatch(1, "screenshot"); require(image.ok && image.screenshot->size == 12, "metadata"); id = image.capture_id; }
    require(visual.dispatch(1, "screenshot.read", {}, id, 0, 6).pixel_hex == "00f8e0071f00", "chunk byte order");
    require(visual.dispatch(1, "screenshot.read", {}, id, UINT64_MAX, 1).error_code == "bad_request", "overflow offset");
    require(visual.dispatch(1, "screenshot.read", {}, id, 11, 2).error_code == "bad_request", "out of bounds");
    require(visual.dispatch(1, "screenshot.read", {}, id, 0, 513).error_code == "bad_request", "bounded chunks");
    require(visual.dispatch(1, "screenshot.read", {}, id+1, 0, 1).error_code == "invalid_state", "stale capture ID");
    now += 60'000;
    visual.expire_screenshot();
    require(retained.expired(), "idle expiry frees pixels without another read");
    require(visual.dispatch(1, "screenshot.read", {}, id, 0, 1).error_code == "invalid_state" && retained.expired(), "expiry drops memory");
    { auto image = visual.dispatch(1, "screenshot"); id = image.capture_id; }
    require(visual.dispatch(1, "release").ok && retained.expired(), "release frees pixels");
    require(visual.dispatch(1, "screenshot.read", {}, id, 0, 1).error_code == "invalid_state", "released capture rejected");
    { auto image = visual.dispatch(1, "screenshot"); id = image.capture_id; }
    require(mode.set_enabled(false).has_value(), "mode off");
    require(visual.dispatch(1, "screenshot.read", {}, id, 0, 1).error_code == "developer_mode_off" && retained.expired(), "mode off drops private pixels");
    require(mode.set_enabled(true).has_value(), "mode re-enable");
    (void)visual.dispatch(1, "screenshot"); visual.clear_screenshot();
    require(retained.expired(), "disconnect cleanup drops capture");
    std::cout << "PASS: full-frame coverage, stride, gated chunks, identity, bounds and cleanup\n";
}
