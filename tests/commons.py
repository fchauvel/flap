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
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock

from flap.engine import Flap
from flap.ui import UI, Factory, Controller
from flap.substitutions.factory import ProcessorFactory
from flap.util.oofs import InMemoryFileSystem
from flap.util.path import TEMP


class TexFile:

    def __init__(self, name, content):
        self._name = name
        self._content = content

    @property
    def path(self):
        return self._name

    @property
    def content(self):
        return self._content

    def __eq__(self, other):
        if not isinstance(other, TexFile):
            return False
        return self._name == other._name and self._content == other._content

    def __hash__(self):
        return hash((self._name, self._content))


class LatexProject:

    @staticmethod
    def extract_from_directory(root):
        files = LatexProject._collect_files_from(root, root)
        return LatexProject(*files)

    @staticmethod
    def _collect_files_from(anchor, directory):
        files = []
        for any_file in directory.files():
            if any_file.is_directory():
                files += LatexProject._collect_files_from(anchor, any_file)
            else:
                path = str(any_file.path().relative_to(anchor.path()))
                files.append(TexFile(path, any_file.content()))
        return files

    def __init__(self, *files):
        self._files = {each_file.path: each_file for each_file in files}

    @property
    def files(self):
        return self._files

    def __hash__(self):
        return hash(self._files)

    def __eq__(self, other):
        if not isinstance(other, LatexProject):
            return False
        return len(set(self._files.items()) - set(other._files.items())) == 0

    def setup(self, file_system, anchor):
        for (path, file) in self.files.items():
            location = anchor / path
            file_system.create_file(location, file.content)

    def assert_is_equivalent_to(self, other):
        self._verify_missing_files(other)
        self._verify_extraneous_files(other)
        self._verify_different_files(other)

    def _verify_different_files(self, other):
        for (path, file) in self.files.items():
            assert path in other.files and file == other.files[path], \
                self.CONTENT_MISMATCH.format(file=path, expected=file.content, actual=other.files[path].content)

    CONTENT_MISMATCH = "Content mismatch for {file}\nExpected:\n'{expected}'\nbut found:\n'{actual}'"

    def _verify_missing_files(self, other):
        for path in self.files:
            assert path in other.files, self.MISSING_FILE.format(file=path)

    MISSING_FILE = "Missing file '{file}'!"

    def _verify_extraneous_files(self, other):
        for path in other.files:
            assert path in self.files, self.UNEXPECTED_FILE.format(file=path)

    UNEXPECTED_FILE = "Unexpected file '{file}'!"


class LatexProjectBuilder:

    def __init__(self):
        self._files = []

    def build(self):
        return LatexProject(*self._files)

    def with_main_file(self, content):
        self._files.append(TexFile(self.MAIN_FILE, content))
        return self

    MAIN_FILE = "main.tex"

    def with_merged_file(self, content):
        self._files.append(TexFile(self.MERGED_FILE, content))
        return self

    MERGED_FILE = "merged.tex"

    def with_file(self, path, content):
        self._files.append(TexFile(path, content))
        return self

    def with_image(self, path):
        self._files.append(TexFile(path, self.IMAGE_CONTENT.format(key=path.replace("/", "_"))))
        return self

    IMAGE_CONTENT = "IMAGE DATA FOR {key}"

def a_project():
    return LatexProjectBuilder()

class FlapTestCase:

    def __init__(self, name, project, expected, skipped=False):
        if not len or len(name) == 0:
            raise ValueError("Invalid test case name (found '%s')" % name)
        self._name = name
        self._project = project
        self._expected = expected
        self._is_skipped = skipped

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        return self._project

    @property
    def expected(self):
        return self._expected

    @property
    def is_skipped(self):
        return self._is_skipped

    def run_with(self, runner):
        runner.test(self._name, self._project, self._expected)

    def __eq__(self, other):
        if not isinstance(other, FlapTestCase):
            return False
        return self._name == other._name and \
               self._project == other._project and \
               self._expected == other._expected and \
               self._is_skipped == other._is_skipped


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
    SKIPPED_KEY = "skipped"

    def detect_test_case(self, file):
        return file.has_extension_from(self.YAML_EXTENSIONS)

    def extract_from(self, file):
        content = yaml.load(StringIO(file.content()))
        arguments = [self._extract_name_from(content),
                     self._extract_project_from(content),
                     self._extract_expected_from(content),
                     self._extract_is_skipped_from(content)]
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

    def _extract_is_skipped_from(self, content):
        if self.SKIPPED_KEY not in content:
            return False
        else:
            return content[self.SKIPPED_KEY]


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


class TestRunner:

    def __init__(self, file_system, directory, ui=UI(StringIO())):
        self._file_system = file_system
        self._directory = directory
        self._ui = ui

    def test(self, name, project, expected):
        self._setup(name, project)
        self._move_to(name)
        self._run_flap(name)
        self._verify(name, expected)

    def _setup(self, name, project):
        project.setup(self._file_system, self._test_location(name))

    def _test_location(self, name):
        return self._directory / self._escape(name) / "project"

    @staticmethod
    def _escape(name):
        return name\
            .replace(" ", "_")\
            .replace("\\", "_")

    def _root_file(self, name):
        return self._test_location(name) / "main.tex"

    def _output_path(self, name):
        return self._directory / self._escape(name) / "flatten"

    def _destination(self, name):
        return self._output_path(name)

    def _run_flap(self, name):
        pass

    def _move_to(self, name):
        self._file_system.move_to_directory(self._test_location(name))

    def _verify(self, name, expected):
        output = self._file_system.open(self._output_path(name))
        actual = LatexProject.extract_from_directory(output)
        expected.assert_is_equivalent_to(actual)


class AcceptanceTestRunner(TestRunner):

    def __init__(self, file_system, directory, ui):
        super().__init__(file_system, directory, ui)

    def _run_flap(self, name):
        factory = Factory(self._file_system, self._ui)
        controller = Controller(factory)
        controller.run(self._arguments(name))

    def _arguments(self, name):
        return ["__main.py__", str(self._root_file(name)), str(self._destination(name))]


class UnitTestRunner(TestRunner):

    def __init__(self, file_system, directory, ui):
        super().__init__(file_system, directory, ui)

    def _run_flap(self, name):
        flap = Flap(self._file_system, ProcessorFactory(), listener=self._ui)
        flap.flatten(self._root_file(name), self._destination(name))

    def _destination(self, name):
        return self._output_path(name)


class FlapTest(TestCase):

    TEST_CASE_NAME = "unit_test"

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._ui = MagicMock()
        self._runner = UnitTestRunner(self._file_system, TEMP / "flap" , self._ui)
        self._assume = None
        self._expect = a_project()
        self._test_case = None

    def _do_test_and_verify(self):
        self._test_case = FlapTestCase(self.TEST_CASE_NAME, self._assume.build(), self._expect.build())
        self._test_case.run_with(self._runner)

    def _verify(self):
        self._test_case.verify(self._runner)

    def _verify_ui_reports_fragment(self, file_name, line_number, excerpt):
        fragment = self._ui.on_fragment.call_args[0][0]
        self.assertEqual(fragment.file().fullname(), file_name)
        self.assertEqual(fragment.line_number(), line_number)
        self.assertEqual(fragment.text().strip(), excerpt)


