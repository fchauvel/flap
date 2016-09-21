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

from flap.path import Path


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

    def setup(self, file_system):
        for (path, file) in self.files.items():
            file_system.create_file(Path.fromText(path), file.content)

    def difference_with(self, other):
        differences = self._missing_files(other)
        differences += self._different_files(other)
        differences += self._extraneous_files(other)
        return differences

    def _different_files(self, other):
        return [DifferentContent(other.files[path]) for (path, file) in self.files.items()
                if path in other.files and file != other.files[path]]

    def _missing_files(self, other):
        return [MissingFile(file) for (path, file) in self.files.items() if path not in other.files]

    def _extraneous_files(self, other):
        return [ExtraFile(file) for (path, file) in other.files.items() if path not in self.files]


class MissingFile:

    def __init__(self, file):
        self._file = file

    def __eq__(self, other):
        if not isinstance(other, MissingFile): return False
        return self._file == other._file


class ExtraFile:
    def __init__(self, file):
        self._file = file

    def __eq__(self, other):
        if not isinstance(other, ExtraFile): return False
        return self._file == other._file


class DifferentContent:
    def __init__(self, file):
        self._file = file

    def __eq__(self, other):
        if not isinstance(other, DifferentContent): return False
        return self._file == other._file