"""Run the production Card presenter against a fake external GUI port."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
NAVIGATION = COMPONENT.parent / 'espocket_navigation'
STUB = r'''
#pragma once
#include <expected>
#include <functional>
#include <memory>
#include <string>
#include <string_view>
#include <vector>
namespace esp_brookesia::gui {
using DocumentId = unsigned;
enum class GuiLayer { Default };
enum class MountStackMode { Stack };
struct MountTarget { std::string display_id; GuiLayer layer; MountStackMode mount_mode; int z_order; };
struct ScopedConnection {
    std::shared_ptr<int> lifetime;
    bool connected() const { return bool(lifetime); }
};
}
namespace esp_brookesia::system::core {
struct SystemGuiAccess {
    bool load_ok = true, mount_ok = true, subscribe_ok = true;
    int loaded = 0, unloaded = 0, mounted = 0, unmounted = 0;
    std::vector<std::function<void(int)>> callbacks;
    std::vector<std::weak_ptr<int>> subscriptions;
    std::vector<std::string> texts;
    std::expected<gui::DocumentId, std::string> load_json(std::string_view, std::string_view, std::string_view) {
        if (!load_ok) return std::unexpected("load_failed");
        ++loaded; return 17;
    }
    bool unload(gui::DocumentId id) { if (id != 17) return false; ++unloaded; return true; }
    std::expected<int, std::string> mount_screen(gui::DocumentId id, std::string_view path, const gui::MountTarget &) {
        if (id != 17 || path != "/card" || !mount_ok) return std::unexpected("mount_failed");
        ++mounted; return 1;
    }
    bool unmount_screen(gui::DocumentId id, std::string_view path) {
        if (id != 17 || path != "/card") return false;
        ++unmounted; return true;
    }
    gui::ScopedConnection subscribe_action(gui::DocumentId, std::string_view, std::function<void(int)> callback) {
        if (!subscribe_ok) return {};
        callbacks.push_back(std::move(callback));
        auto lifetime = std::make_shared<int>(0); subscriptions.push_back(lifetime); return {lifetime};
    }
    std::expected<void, std::string> set_text(gui::DocumentId id, std::string_view path, std::string_view text) {
        if (id != 17) return std::unexpected("wrong_document");
        texts.push_back(std::string(path) + ":" + std::string(text)); return {};
    }
};
}
'''
TEST = r'''
#include "card_document.hpp"
#include <cassert>
using namespace espocket;
using esp_brookesia::system::core::SystemGuiAccess;
struct Model : CardModel {
    bool show_ok = true, refresh_ok = true;
    int refreshes = 0, pauses = 0, actions = 0;
    CardView view() const override { return {"{}", "", "/card", {"increment"}}; }
    bool on_show(CardUi &) noexcept override { return show_ok; }
    bool on_refresh(CardUi &ui) noexcept override { ++refreshes; return refresh_ok && ui.set_text("/card/value", "fresh"); }
    void on_pause() noexcept override { ++pauses; }
    bool on_action(CardUi &, std::string_view value) noexcept override { ++actions; return value == "increment"; }
};
int main() {
    SystemGuiAccess gui;
    std::vector<std::string> queued;
    unsigned generation = 1;
    auto sink = [&] { return [&, captured = generation](std::string action) {
        queued.push_back(std::to_string(captured) + ":" + action);
    }; };
    assert(!CardDocument::create(gui, nullptr, sink));
    gui.load_ok = false;
    assert(!CardDocument::create(gui, std::make_unique<Model>(), sink));
    gui.load_ok = true;
    auto model = std::make_unique<Model>(); auto *observed = model.get();
    auto doc = CardDocument::create(gui, std::move(model), sink);
    assert(doc && gui.loaded == 1);
    assert(!doc->set_text("/card/value", "paused"));
    gui.mount_ok = false;
    assert(!doc->show() && gui.mounted == 0);
    gui.mount_ok = true;
    assert(doc->show() && doc->refresh());
    assert(observed->refreshes == 1 && gui.texts.back() == "/card/value:fresh");
    gui.callbacks[0](0);
    assert(queued.back() == "1:increment" && observed->actions == 0); // GUI only enqueues.
    assert(doc->action("increment") && observed->actions == 1);
    auto old_callback = gui.callbacks[0];
    doc->pause();
    assert(gui.subscriptions[0].expired() && gui.subscriptions[1].expired());
    assert(observed->pauses == 1 && gui.unmounted == 1);
    assert(!doc->refresh() && !doc->action("increment") && !doc->set_text("/card/value", "old"));
    generation = 2;
    assert(doc->show() && doc->refresh());
    old_callback(0); assert(queued.back() == "1:increment"); // Owner rejects old generation.
    gui.callbacks[2](0); assert(queued.back() == "2:increment");
    doc.reset();
    assert(gui.unloaded == 1 && gui.unmounted == 2 && gui.subscriptions[2].expired());
    auto failing = std::make_unique<Model>(); failing->show_ok = false;
    auto failed = CardDocument::create(gui, std::move(failing), sink);
    assert(!failed->show()); failed->pause();
    assert(gui.unmounted == 3);
    gui.subscribe_ok = false;
    auto disconnected = CardDocument::create(gui, std::make_unique<Model>(), sink);
    assert(!disconnected->show()); disconnected->pause();
    assert(gui.unmounted == 4);
}
'''

class CardDocumentTest(unittest.TestCase):
    def test_document_lifetime_and_action_handoff(self):
        with tempfile.TemporaryDirectory(prefix='espocket-card-document-') as directory:
            root = Path(directory)
            header = root / 'brookesia/system_core/system/gui_access.hpp'
            header.parent.mkdir(parents=True)
            header.write_text(STUB)
            (root / 'test.cpp').write_text(TEST)
            binary = root / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-Wall', '-Wextra', '-Werror',
                '-I', str(root), '-I', str(COMPONENT / 'include'), '-I', str(COMPONENT / 'src'),
                '-I', str(NAVIGATION / 'include'), str(COMPONENT / 'src/card_document.cpp'),
                str(root / 'test.cpp'), '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)

if __name__ == '__main__':
    unittest.main()
