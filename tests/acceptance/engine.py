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

import yaml
from flap.ui import Controller, Factory, UI
from io import StringIO
from tests.acceptance.latex_project import TexFile, LatexProject


class YamlCodec:
    """
    Transform a YAML snippet in a FlapTestCase, or raises an error if
    it is not possible
    """

    YAML_EXTENSIONS = ["yml", "yaml"]

    NAME_KEY = "name"
    EXPECTED_KEY = "expected"
    PROJECT_KEY = "project"
    PATH_KEY = "path"
    CONTENT_KEY = "content"

    def detect_test_case(self, file):
        return file.has_extension_from(self.YAML_EXTENSIONS)

    def extract_from(self, file):
        content = yaml.load(StringIO(file.content()))
        arguments = [self._extract_name_from(content),
                     self._extract_project_from(content),
                     self._extract_expected_from(content)]
        return FlapTestCase(*arguments)

    def _extract_name_from(self, content):
        if self.NAME_KEY not in content:
            self._handle_missing_key(self.NAME_KEY)
        return content[self.NAME_KEY]

    @staticmethod
    def _handle_missing_key(key):
        raise InvalidYamlTestCase("Invalid YAML: Expecting key '%s'!" % key)

    def _extract_project_from(self, content):
        if self.PROJECT_KEY not in content:
            self._handle_missing_key(self.PROJECT_KEY)
        return self._extract_latex_project_from(content[self.PROJECT_KEY])

    def _extract_expected_from(self, content):
        if self.EXPECTED_KEY not in content:
            self._handle_missing_key(self.EXPECTED_KEY)
        return self._extract_latex_project_from(content[self.EXPECTED_KEY])

    def _extract_latex_project_from(self, project):
        project_files = []
        for each_file in project:
            project_files.append(self._extract_tex_file(each_file))
        return LatexProject(*project_files)

    def _extract_tex_file(self, entry):
        return TexFile(self._extract_path(entry),self._extract_content(entry))

    def _extract_path(self, entry):
        if self.PATH_KEY not in entry:
            self._handle_missing_key(self.PATH_KEY)
        return entry[self.PATH_KEY]

    def _extract_content(self, entry):
        if self.CONTENT_KEY not in entry:
            self._handle_missing_key(self.CONTENT_KEY)
        return entry[self.CONTENT_KEY].strip()


class InvalidYamlTestCase(Exception):

    def __init__(self, message):
        super().__init__(message)


class FileBasedTestRepository:
    """
    Search the file systems for files that can be read by the given codecs
    """

    def __init__(self, file_system, path, codec):
        self._path = path
        self._file_system = file_system
        self._codec = codec

    def fetch_all(self):
        directory = self._file_system.open(self._path)
        return self._fetch_all_from(directory)

    def _fetch_all_from(self, directory):
        test_cases = []
        for any_file in directory.files():
            if any_file.is_directory():
                test_cases.extend(self._fetch_all_from(any_file))
            else:
                if self._codec.detect_test_case(any_file):
                    test_case = self._codec.extract_from(any_file)
                    test_cases.append(test_case)
        return test_cases


class FlapTestCase:

    def __init__(self, name, project, expected):
        if not len or len(name) == 0:
            raise ValueError("Invalid test case name (found '%s')" % name)
        self._name = name
        self._project = project
        self._expected = expected

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        return self._project

    @property
    def expected(self):
        return self._expected

    def run_with(self, runner):
        return runner.test(self._name, self._project, self._expected)

    def __eq__(self, other):
        if not isinstance(other, FlapTestCase):
            return False
        return self._name == other._name and \
               self._project == other._project and \
               self._expected == other._expected


class Verdict:

    def __init__(self, test_case_name):
        self._test_case = test_case_name

    @staticmethod
    def passed(test_case):
        return SuccessVerdict(test_case)

    @staticmethod
    def error(test_case, caught_exception):
        return ErrorVerdict(test_case, caught_exception)

    @staticmethod
    def failed(test_case, differences):
        return FailedVerdict(test_case, differences)


class SuccessVerdict(Verdict):

    def __init__(self, test_case_name):
        super().__init__(test_case_name)

    def accept(self, visitor):
        visitor.on_success(self._test_case)


class FailedVerdict(Verdict):

    def __init__(self, test_case_name, differences):
        super().__init__(test_case_name)
        self._differences = differences

    def accept(self, visitor):
        visitor.on_failure(self._test_case, self._differences)


class ErrorVerdict(Verdict):

    def __init__(self, test_case_name, caught_exception):
        super().__init__(test_case_name)
        self._caught_exception = caught_exception

    def accept(self, visitor):
        visitor.on_error(self._test_case, self._caught_exception)


class TestRunner:
    """
    Run a list of FlapTestCase
    """

    def __init__(self, file_system, directory):
        self._file_system = file_system
        self._ui = UI(StringIO())
        self._directory = directory

    def test(self, name, project, expected):
        directory = self._directory / self._escape(name)
        try:
            project_path = directory / "project"
            output_path = directory / "flatten"
            project.setup(self._file_system, project_path)
            self._run_flap(project_path / "main.tex", output_path)
            output = self._file_system.open(output_path)
            actual = LatexProject.extract_from_directory(output)
            return self._verify(name, expected, actual)

        except Exception as error:
            return Verdict.error(name, error)

    @staticmethod
    def _escape(name):
        return name.replace(" ", "_")

    def _run_flap(self, root_latex_file, output_directory):
        factory = Factory(self._file_system, self._ui)
        arguments = ["__main.py__", str(root_latex_file), str(output_directory)]
        Controller(factory).run(arguments)

    def _verify(self, test_case_name, expected, actual):
        differences = expected.difference_with(actual)
        if len(differences) == 0:
            return Verdict.passed(test_case_name)
        return Verdict.failed(test_case_name, differences)


class Acceptor:

    TEST_PASS = "PASS"
    TEST_FAILED = "FAILED"
    TEST_ERROR = "ERROR"
    TEST_CASE = "{name:45}{verdict:10}\n"
    HORIZONTAL_LINE = "----------\n"
    SUMMARY = "{total} tests ({passed} success ; {failed} failure ; {error} error ; 0 skipped)\n"
    NO_TEST_FOUND = "Could not find any acceptance test.\n"
    MISSING_FILE = "\t - Could not find file '{file_name}'\n"
    UNEXPECTED_FILE = "\t - Unexpected file '{file_name}'\n"
    CONTENT_MISMATCH = "\t - Content mismatch for file '{file_name}'\n"

    def __init__(self, repository, runner, output):
        self._test_case_repository = repository
        self._runner = runner
        self._output = output
        self._counter = {
            self.TEST_PASS: 0,
            self.TEST_FAILED: 0,
            self.TEST_ERROR: 0
        }

    def check(self):
        self._show_header()
        for each_test_case in self._test_case_repository.fetch_all():
            verdict = each_test_case.run_with(self._runner)
            verdict.accept(self)
        self._show_summary()

    def _show_header(self):
        self._show(self.TEST_CASE, name="Test case name", verdict="Status")
        self._show(self.HORIZONTAL_LINE)

    def _show_summary(self):
        if self._no_test_case_found:
            self._show(self.NO_TEST_FOUND)
        else:
            self._show(self.HORIZONTAL_LINE)
            self._show(self.SUMMARY,
                       total=self._test_case_count,
                       passed=self._counter[self.TEST_PASS],
                       failed=self._counter[self.TEST_FAILED],
                       error=self._counter[self.TEST_ERROR])

    @property
    def _no_test_case_found(self):
        return self._test_case_count == 0

    @property
    def _test_case_count(self):
        return sum(self._counter.values())

    def on_success(self, test_case_name):
        self._counter[self.TEST_PASS] += 1
        self._show(self.TEST_CASE, name=test_case_name, verdict=self.TEST_PASS)

    def on_failure(self, test_case_name, differences):
        self._counter[self.TEST_FAILED] += 1
        self._show(self.TEST_CASE, name=test_case_name, verdict=self.TEST_FAILED)
        for each_difference in differences:
            each_difference.accept(self)

    def on_missing_file(self, file):
        self._show(self.MISSING_FILE, file_name=str(file.path))

    def on_extraneous_file(self, file):
        self._show(self.UNEXPECTED_FILE, file_name=str(file.path))

    def on_content_mismatch(self, file):
        self._show(self.CONTENT_MISMATCH, file_name=str(file.path))

    def on_error(self, test_case_name, caught_exception):
        self._counter[self.TEST_ERROR] += 1
        self._show(self.TEST_CASE, name=test_case_name, verdict=self.TEST_ERROR)

    def _show(self, message, **values):
        self._output.write(message.format(**values))
