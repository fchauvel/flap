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

import re
import tempfile


class Path:
    
    @staticmethod
    def fromText(text):
        pattern = re.compile("[\\\\/]+")
        parts = [Unit(eachPart) for eachPart in pattern.split(text)]
        if parts[-1].is_root(): # Remove the last one, if it is "" (e.g., in project/img/)
            parts = parts[:-1]
        return Path(parts)

    def __init__(self, parts):
        if not parts:
            raise ValueError("Invalid path, no part given")
        self._parts = [part for (index, part) in enumerate(parts) if not (part.is_current_directory() and index > 0)]

    def resource(self):
        return self._parts[-1]

    def fullname(self):
        return self.resource().fullname()

    def basename(self):
        return self.resource().basename()

    def extension(self):
        return self.resource().extension()

    def has_extension(self, extension=None):
        if extension:
            return self.resource().has_extension(extension)
        else:
            return self.resource().has_any_extension()

    def container(self):
        if len(self._parts) == 1:
            if self._parts[0].is_root():
                raise ValueError("The root directory has no parent")
            else:
                return Path([Unit(".")])
        return Path(self._parts[:-1])

    def isRoot(self):
        return self.resource().is_root()

    def is_absolute(self):
        return self._parts[0].is_root()

    def absolute_from(self, current_directory):
        parts = self.parts()
        if parts[0].is_current_directory():
            parts = current_directory.parts() + parts[1:]
        elif parts[0].is_parent_directory():
            parts = current_directory.container().parts() + parts[1:]
        elif not parts[0].is_root():
            parts = current_directory.parts() + parts
        return Path.fromText("/".join([each.fullname() for each in parts]))

    def relative_to(self, location):
        position = 0
        while position < len(location._parts) and self._parts[position] == location._parts[position]:
            position += 1
        return Path(self._parts[position:])

    def without_extension(self):
        return Path(self._parts[:-1] + [Unit(self._parts[-1].basename())])

    def parts(self):
        return self._parts
    
    def __contains__(self, other): 
        return self != other and self.__str__() in other.__str__()

    def __truediv__(self, other):
        if isinstance(other, str):
            return Path(self._parts + Path.fromText(other)._parts)
        elif isinstance(other, Path):
            return Path(self._parts + other._parts)

    def __repr__(self):
        return "/".join([eachPart.fullname() for eachPart in self._parts])
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return isinstance(other, Path) and self._parts == other._parts

    def __hash__(self):
        return self.__str__().__hash__()


class Unit:
    """
    A fragment of path, such as home, dir amd test.txt in /home/dir/test.txt
    """

    NAMES = re.compile("(.+)\\.([^\\.]+)$")
    DRIVE = re.compile("\\w\:")

    def __init__(self, name):
        self._name = name.replace("\n", "").strip()
        self._match = re.match(Unit.NAMES, self._name)

    def fullname(self):
        return self._name

    def basename(self):
        if not self.has_any_extension():
            raise ValueError("No basename in '%s'" % self.fullname())
        return self._match.group(1)

    def extension(self):
        if not self.has_any_extension():
            raise ValueError("No extension in '%s'" % self.fullname())
        return self._match.group(2)

    def has_any_extension(self):
        return self._match and not self._match.group(2) is None

    def has_extension(self, extension):
        return self.has_any_extension() and self.extension().lower() == extension.lower()

    def is_root(self):
        return re.match(Unit.DRIVE, self._name) or self._name == ""

    def is_current_directory(self):
        return self._name == "."

    def is_parent_directory(self):
        return self._name == ".."

    def __repr__(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, Unit) and other._name == self._name

    def __hash__(self):
        return self._name.__hash__()


ROOT = Path([Unit("")])

TEMP = Path.fromText(tempfile.gettempdir())

CURRENT_DIRECTORY = Path([Unit(".")])
