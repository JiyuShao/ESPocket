"""Run production Runtime navigation and Card storage JSON boundaries."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
BOOST = COMPONENT.parents[1] / 'managed_components/espressif__esp-boost/src'


class RuntimeAdapterTest(unittest.TestCase):
    def test_json_and_navigation_contract(self):
        self.run_contract("test_runtime_page_adapter.cpp")

    def test_card_configuration_storage(self):
        self.run_contract("test_card_configuration_store.cpp")

    def test_declarative_card_contract(self):
        self.run_contract("test_declarative_card.cpp")

    def run_contract(self, source):
        with tempfile.TemporaryDirectory(prefix='espocket-runtime-pages-') as directory:
            temp = Path(directory)
            (temp / 'boost.cpp').write_text('#include <boost/json/src.hpp>\n')
            binary = temp / 'test'
            subprocess.run([
                os.environ.get('CXX', 'clang++'), '-std=c++23', '-pthread', '-DBOOST_NO_USER_CONFIG',
                '-I', str(COMPONENT / 'include'), '-I', str(BOOST),
                str(COMPONENT / 'src/page_navigator.cpp'),
                str(COMPONENT / 'src/page_declaration_codec.cpp'),
                str(COMPONENT / 'src/runtime_page_adapter.cpp'),
                str(COMPONENT / 'src/navigation_request_queue.cpp'),
                str(COMPONENT / 'src/card_registry.cpp'),
                str(COMPONENT / 'src/card_session.cpp'),
                str(COMPONENT / 'src/declarative_card.cpp'),
                str(COMPONENT / 'src/card_configuration_store.cpp'),
                str(COMPONENT / 'test' / source), str(temp / 'boost.cpp'),
                '-o', str(binary),
            ], check=True)
            args = [str(binary)]
            if source == "test_declarative_card.cpp":
                sample = COMPONENT.parents[1] / "runtime_apps/hello/src/res"
                args += [str(sample / "navigation.json"), str(sample / "cards.json")]
            subprocess.run(args, check=True)


if __name__ == '__main__':
    unittest.main()
