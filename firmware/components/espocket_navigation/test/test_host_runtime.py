"""Run the real versioned JSON boundary and Runtime adapter against the shared Navigator."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1]
BOOST = COMPONENT.parents[1] / 'managed_components/espressif__esp-boost/src'


class RuntimeAdapterTest(unittest.TestCase):
    def test_json_and_navigation_contract(self):
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
                str(COMPONENT / 'test/test_runtime_page_adapter.cpp'), str(temp / 'boost.cpp'),
                '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
