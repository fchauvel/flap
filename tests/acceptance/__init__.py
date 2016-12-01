#
# This file is part of Flap.
#
# Flap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Flap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flap.  If not, see <http://www.gnu.org/licenses/>.
#


from unittest import TestCase, TestSuite, main

from flap.util.path import Path
from flap.util.oofs import OSFileSystem
from tests.commons import EndToEndRunner
from tests.acceptance.yaml import FileBasedTestRepository, YamlCodec


class Generator:

    def __init__(self, repository, runner):
        self._repository = repository
        self._runner = runner

    def create_execution(self, test_case):
        def run(this):
            if test_case.is_skipped:
                this.skipTest("Test skipped, according to its YAML description")
            else:
                test_case.run_with2(self._runner)
        return run

    def test_class(self):
        test_cases = self._repository.fetch_all()
        methods = { "test " + each_case.name: self.create_execution(each_case) for each_case in test_cases }
        return type("YAMLParserTests", (TestCase,), methods)


def load_tests(loader, tests, pattern):
    file_system = OSFileSystem()
    repository = FileBasedTestRepository(file_system, Path.fromText("tests/acceptance/scenarios"), YamlCodec())
    runner = EndToEndRunner(file_system)
    generate = Generator(repository, runner)
    suite = TestSuite()
    tests = loader.loadTestsFromTestCase(generate.test_class())
    suite.addTests(tests)
    return suite


if __name__ == "__main__":
    main()