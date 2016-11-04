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
from tests.latex_project import LatexProject, TexFile, FlapTestCase, Fragment


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

    KEY_OUTPUTS = "outputs"
    KEY_FILE = "file"
    KEY_LINE = "line"
    KEY_COLUMN = "column"
    KEY_CODE = "code"

    def detect_test_case(self, file):
        return file.has_extension_from(self.YAML_EXTENSIONS)

    def extract_from(self, file):
        content = yaml.load(StringIO(file.content()))
        arguments = [self._extract_name_from(content),
                     self._extract_project_from(content),
                     self._extract_expected_from(content),
                     self._extract_is_skipped_from(content),
                     self._extract_outputs(content)]
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

    def _extract_outputs(self, yaml_map):
        if self.KEY_OUTPUTS not in yaml_map:
            return []
        else:
            return self._extract_entries(yaml_map["outputs"])

    def _extract_entries(self, yaml_list):
        entries = []
        for each_entry in yaml_list:
            entries.append(self._extract_entry(each_entry))
        return entries

    def _extract_entry(self, yaml_map):
        arguments = [
            self._extract_file_name(yaml_map),
            self._extract_line_number(yaml_map),
            self._extract_column_number(yaml_map),
            self._extract_latex_code(yaml_map)
        ]
        return Fragment(*arguments)

    def _extract_file_name(self, entry):
        if self.KEY_FILE not in entry:
            self._handle_missing_key(self.KEY_FILE)
        return entry[self.KEY_FILE]

    def _extract_line_number(self, entry):
        if self.KEY_LINE not in entry:
            self._handle_missing_key(self.KEY_LINE)
        return int(entry[self.KEY_LINE])

    def  _extract_column_number(self, entry):
        if self.KEY_COLUMN not in entry:
            self._handle_missing_key(self.KEY_COLUMN)
        return int(entry[self.KEY_COLUMN])

    def _extract_latex_code(self, entry):
        if self.KEY_CODE not in entry:
            self._handle_missing_key(self.KEY_CODE)
        return entry[self.KEY_CODE]


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
