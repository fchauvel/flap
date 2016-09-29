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

