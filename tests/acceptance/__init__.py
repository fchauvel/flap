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

from flap.util.path import TEMP, Path
from flap.util.oofs import OSFileSystem
from tests.acceptance.engine import FileBasedTestRepository, YamlCodec, TestRunner

def create_description(text):
    def short_description(self):
        return text
    return short_description

def create_test(a, b, c):
    def test(self):
        print("a={0}, b={1}, c={2}", a, b, c)
        self.assertEqual(a, b+c)
    return test


class Generator:

    def __init__(self, repository, runner):
        self._repository = repository
        self._runner = runner

    def create_execution(self, test_case):
        def run(this):
            if test_case.is_skipped:
                this.skipTest("Test skipped, according to its YAML description")
            else:
                test_case.run_with(self._runner)
        return run

    def test_class(self):
        test_cases = self._repository.fetch_all()
        methods = { "test " + each_case.name: self.create_execution(each_case) for each_case in test_cases }
        return type("YAMLAcceptanceTests", (TestCase,), methods)


def load_tests(loader, tests, pattern):
    file_system = OSFileSystem()
    repository = FileBasedTestRepository(file_system, Path.fromText("tests/acceptance/tests"), YamlCodec())
    runner = TestRunner(file_system, TEMP / "flap" / "acceptance")
    generate = Generator(repository, runner)
    suite = TestSuite()
    tests = loader.loadTestsFromTestCase(generate.test_class())
    suite.addTests(tests)
    return suite


if __name__ == "__main__":
    main()