#include <array>
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include "espocket/test_protocol.hpp"

void require(bool ok, const char *message) {
    if (!ok) { std::cerr << message << '\n'; std::exit(1); }
}
int main() {
    const auto allocate = [](size_t n) {
        require(n <= 1024, "no full-frame allocation under fragmentation");
        return std::shared_ptr<uint8_t>(new uint8_t[n], std::default_delete<uint8_t[]>());
    };
    espocket::ScreenshotPixels compact(466, 466, allocate);
    std::array<uint8_t, 932> solid{};
    for (size_t p = 0; p < 466; ++p) solid[p * 2 + 1] = 248;
    for (size_t y = 0; y < 466; ++y) require(compact.write(y * solid.size(), solid), "solid frame capture");
    require(compact.stored_size() == 466 * 4, "flat rows use lossless runs");
    std::array<uint8_t, 512> chunk{};
    require(compact.read(931, chunk) && chunk[0] == 248 && chunk[1] == 0 && chunk[511] == 0,
            "unaligned cross-row protocol chunk preserves RGB565 order");
    for (size_t i = 0; i < solid.size(); ++i) solid[i] = static_cast<uint8_t>(i);
    require(compact.write(932, solid), "high entropy row switches to raw");
    std::array<uint8_t, 932> decoded{};
    require(compact.read(932, decoded) && decoded == solid, "raw fallback is lossless");
    const std::array<uint8_t, 4> overlap{19, 20, 21, 22};
    require(compact.write(931, overlap) && compact.read(931, chunk) &&
            std::equal(overlap.begin(), overlap.end(), chunk.begin()), "overlapping partial flush can edit compressed and raw rows");
    require(!compact.write(SIZE_MAX, solid) && !compact.read(compact.size() - 1, chunk), "storage range overflow rejected");
    espocket::ScreenshotPixels exhausted(3, 2, [](size_t) { return std::shared_ptr<uint8_t>{}; });
    std::array<uint8_t, 1> failed_coverage{};
    espocket::ScreenshotAssembly failed_storage(3, 2, exhausted, failed_coverage);
    require(!failed_storage.append(0, 0, 2, 1, solid, 6) && !failed_storage.complete(), "allocation failure cannot report complete frame");

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
    std::weak_ptr<espocket::ScreenshotPixels> retained;
    espocket::TestProtocol visual(mode, "visual-image", {}, {}, [] { return std::expected<void, std::string>{}; }, {},
        [&]() -> std::expected<espocket::TestScreenshot, std::string> {
            ++calls;
            auto bytes = std::make_shared<espocket::ScreenshotPixels>(3, 2, [](size_t n) {
                return std::shared_ptr<uint8_t>(new uint8_t[n], std::default_delete<uint8_t[]>());
            });
            const std::array<uint8_t, 12> raw{0,248,224,7,31,0};
            require(bytes->write(0, raw), "fixture writes pixels");
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
