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

    def assert_is_equivalent_to(self, expectation):
        self._verify_missing_files(expectation)
        self._verify_extraneous_files(expectation)
        self._verify_different_files(expectation)

    def _verify_different_files(self, expectation):
        for (path, file) in self.files.items():
            assert path in expectation.files and file == expectation.files[path], \
                self.CONTENT_MISMATCH.format(file=path, expected=expectation.files[path].content, actual=file.content)

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


def a_project():
    return LatexProjectBuilder()


class Fragment:

    KEY_FILE = "file"
    KEY_LINE = "line"
    KEY_COLUMN = "column"
    KEY_CODE = "code"

    def __init__(self, file_name, line, column, code):
        self._file_name = file_name
        self._line = line
        self._column = column
        self._code = code

    @property
    def as_dictionary(self):
        return {self.KEY_FILE: self._file_name,
                self.KEY_LINE: self._line,
                self.KEY_COLUMN: self._column,
                self.KEY_CODE: self._code}

    def __eq__(self, other):
        if not isinstance(other, Fragment):
            return False
        return self._file_name == other._file_name and \
               self._line == other._line and \
               self._column == other._column and \
               self._code == other._code


class FlapTestCase:

    def __init__(self, name, project, expected, invocation=None, skipped=False, output=None):
        if not len or len(name) == 0:
            raise ValueError("Invalid test case name (found '%s')" % name)
        self._name = name
        self._project = project
        self._expected = expected
        self._invocation = invocation or Invocation()
        self._is_skipped = skipped
        self._output = output or []

    @property
    def name(self):
        return self._name

    @property
    def escaped_name(self):
        return self.name.strip().replace(" ", "_")

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

    def run_with2(self, runner):
        runner.test(self)

    def __eq__(self, other):
        if not isinstance(other, FlapTestCase):
            return False
        return self._name == other._name and \
               self._project == other._project and \
               self._expected == other._expected and \
               self._invocation == other._invocation and \
               self._is_skipped == other._is_skipped and \
               self._output == other._output


class Invocation:
    """
    Capture the parameters that can be passed to FLaP via the command line
    """

    DEFAULT_TEX_FILE = "main.tex"

    def __init__(self, tex_file=None):
        self._tex_file = tex_file or str(self.DEFAULT_TEX_FILE)

    @property
    def tex_file(self):
        return self._tex_file

    def __eq__(self, other):
        if not isinstance(other, Invocation):
            return False
        return self._tex_file == other._tex_file