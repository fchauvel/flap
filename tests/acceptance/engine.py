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
from flap.path import Path

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

    def __eq__(self, other):
        if not isinstance(other, FlapTestCase):
            return False
        return self._name == other._name and \
               self._project == other._project and \
               self._expected == other._expected

    def setup(self, file_system):
        for (path, file) in self._project.files.items():
            file_system.create_file(Path.fromText(path), file.content)


class Verdict:
    ERROR = 1
    PASS = 2
    FAILED = 3


class TestRunner:
    """
    Run a list of FlapTestCase
    """

    def __init__(self, test_cases):
        self._test_cases = test_cases

    def run(self):
        results = []
        for each_test_case in self._test_cases:
            try:
                verdict = each_test_case.run()
            except Exception:
                verdict = Verdict.ERROR
            results += [(each_test_case, verdict)]
        return results