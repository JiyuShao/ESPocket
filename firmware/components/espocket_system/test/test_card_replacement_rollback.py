"""Exercise production Card replacement snapshot, commit, and rollback methods."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
SYSTEM_CARDS = ROOT / 'firmware/components/espocket_system/src/system_cards.cpp'
SYSTEM_LIFECYCLE = ROOT / 'firmware/components/espocket_system/src/system_lifecycle.cpp'
NAVIGATION = ROOT / 'firmware/components/espocket_navigation'
BOOST = ROOT / 'firmware/managed_components/espressif__esp-boost/src'


def method(source, start, end):
    text = source.read_text()
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


class CardReplacementRollbackTest(unittest.TestCase):
    def test_persistence_commit_and_rollback_boundaries(self):
        methods = ''.join([
            method(SYSTEM_CARDS, 'void System::remember_replaced_card_state(',
                   '\nstd::expected<void, std::string> System::restore_replaced_card_state('),
            method(SYSTEM_CARDS, 'std::expected<void, std::string> System::restore_replaced_card_state(',
                   '\nstd::vector<CardKey> System::available_cards()'),
            method(SYSTEM_LIFECYCLE, 'std::expected<void, std::string> System::on_app_replacement_committed(',
                   '\nstd::expected<void, std::string> System::on_app_replacement_rolled_back('),
            method(SYSTEM_LIFECYCLE, 'std::expected<void, std::string> System::on_app_replacement_rolled_back(',
                   '\nstd::expected<void, std::string> System::on_app_started('),
        ])
        harness = r'''
#include "espocket/card_configuration_store.hpp"
#include <cassert>
#include <atomic>
#include <memory>
#include <atomic>
#include <optional>
#include <string>
#include <string_view>
namespace esp_brookesia::system::core { struct AppInfo { struct { std::string id = "app.old"; } manifest; }; }
namespace espocket {
struct System {
    struct ReplacedCardState {
        std::string app_id;
        PageDeclaration declaration;
        CardConfiguration configuration;
        bool had_declaration = true;
    };
    std::unique_ptr<CardRegistry> cards_;
    std::unique_ptr<CardConfigurationStore> card_store_;
    std::optional<ReplacedCardState> replaced_card_state_;
    bool card_samples_active_ = false;
    std::atomic<uint64_t> launcher_generation_ = 0;
    bool fail_migration = false;
    CardConfiguration card_configuration() const { return cards_->configuration(); }
    void remember_replaced_card_state(std::string_view app_id);
    std::expected<void, std::string> restore_replaced_card_state(std::string_view app_id);
    std::expected<void, std::string> on_app_replaced(
        const esp_brookesia::system::core::AppInfo &,
        const esp_brookesia::system::core::AppInfo &) {
        if (fail_migration) return std::unexpected("migration_failed");
        return {};
    }
    std::expected<void, std::string> on_app_replacement_committed(
        const esp_brookesia::system::core::AppInfo &,
        const esp_brookesia::system::core::AppInfo &);
    std::expected<void, std::string> on_app_replacement_rolled_back(
        const esp_brookesia::system::core::AppInfo &,
        const esp_brookesia::system::core::AppInfo &);
};
''' + methods + r'''
}
using namespace espocket;
struct Fixture {
    System system;
    std::string persisted;
    unsigned saves = 0;
    bool fail_save = false;
    Fixture() {
        system.cards_ = std::make_unique<CardRegistry>();
        system.card_store_ = std::make_unique<CardConfigurationStore>(
            *system.cards_, [] { return std::expected<std::optional<std::string>, std::string>{std::optional<std::string>{}}; },
            [this](std::string_view json) -> std::expected<void, std::string> {
                ++saves;
                if (fail_save) return std::unexpected("writer_failure");
                persisted = json;
                return {};
            });
    }
};
PageDeclaration old_declaration() {
    return {"app.old", "root", {"root", "detail"}, {{"summary", "root"}, {"control", "detail"}}};
}
PageDeclaration other_declaration() {
    return {"app.other", "root", {"root"}, {{"other", "root"}}};
}
int main() {
    const CardKey summary{"app.old", "summary"}, control{"app.old", "control"}, other{"app.other", "other"};
    const CardConfiguration original{{control, summary}, {other}};
    esp_brookesia::system::core::AppInfo app;

    Fixture commit;
    assert(commit.system.cards_->register_app(old_declaration()));
    assert(commit.system.cards_->register_app(other_declaration()));
    assert(commit.system.card_store_->apply(original));
    commit.saves = 0;
    const auto old_json = commit.persisted;
    commit.system.remember_replaced_card_state("app.old");
    auto reduced = old_declaration(); reduced.cards = {{"control", "detail"}};
    assert(commit.system.cards_->update_app(reduced));
    assert(commit.persisted == old_json && commit.saves == 0);
    assert(commit.system.on_app_replacement_committed(app, app));
    assert(commit.saves == 1 && decode_card_configuration(commit.persisted) == commit.system.cards_->configuration());
    assert(!commit.system.replaced_card_state_);

    Fixture postcommit_failure;
    assert(postcommit_failure.system.cards_->register_app(old_declaration()));
    assert(postcommit_failure.system.cards_->register_app(other_declaration()));
    assert(postcommit_failure.system.card_store_->apply(original));
    const auto retained_json = postcommit_failure.persisted;
    postcommit_failure.saves = 0;
    postcommit_failure.system.remember_replaced_card_state("app.old");
    assert(postcommit_failure.system.cards_->update_app(reduced));
    postcommit_failure.fail_save = true;
    auto persistence_failed = postcommit_failure.system.on_app_replacement_committed(app, app);
    assert(!persistence_failed);
    assert(persistence_failed.error() == "Card update persistence failed: writer_failure");
    assert(postcommit_failure.persisted == retained_json && postcommit_failure.saves == 1);
    assert(postcommit_failure.system.replaced_card_state_); // Explicitly retained for repair; no rollback of committed bytes.

    Fixture rollback;
    assert(rollback.system.cards_->register_app(old_declaration()));
    assert(rollback.system.cards_->register_app(other_declaration()));
    assert(rollback.system.card_store_->apply(original));
    rollback.saves = 0;
    rollback.system.remember_replaced_card_state("app.old");
    assert(rollback.system.cards_->update_app(reduced));
    rollback.system.fail_migration = true;
    auto failed = rollback.system.on_app_replacement_rolled_back(app, app);
    assert(!failed && failed.error() == "migration_failed");
    assert(rollback.system.cards_->declaration("app.old")->cards.size() == 2);
    assert(rollback.system.cards_->configuration() == original);
    assert(decode_card_configuration(rollback.persisted) == original && rollback.saves == 1);

    Fixture no_cards;
    assert(no_cards.system.cards_->register_app(other_declaration()));
    const CardConfiguration other_only{{}, {other}};
    assert(no_cards.system.card_store_->apply(other_only));
    no_cards.saves = 0;
    no_cards.system.remember_replaced_card_state("app.old");
    assert(no_cards.system.cards_->register_app(old_declaration()));
    assert(no_cards.system.cards_->replace_configuration({{summary}, {other}}));
    assert(no_cards.system.on_app_replacement_rolled_back(app, app));
    assert(no_cards.system.cards_->declaration("app.old").error() == CardError::UnknownApp);
    assert(no_cards.system.cards_->configuration() == other_only);
    assert(decode_card_configuration(no_cards.persisted) == other_only && no_cards.saves == 1);
}
'''
        with tempfile.TemporaryDirectory(prefix='espocket-card-replacement-') as directory:
            temp = Path(directory)
            cpp = temp / 'test.cpp'
            boost = temp / 'boost.cpp'
            binary = temp / 'test'
            cpp.write_text(harness)
            boost.write_text('#include <boost/json/src.hpp>\n')
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-DBOOST_NO_USER_CONFIG',
                '-I', str(NAVIGATION / 'include'), '-I', str(BOOST),
                str(cpp), str(NAVIGATION / 'src/page_navigator.cpp'),
                str(NAVIGATION / 'src/card_registry.cpp'),
                str(NAVIGATION / 'src/card_configuration_store.cpp'), str(boost),
                '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
