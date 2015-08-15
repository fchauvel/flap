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

class Path:
    
    @staticmethod
    def fromText(text):
        pattern = re.compile("[\\\\/]+")
        parts = pattern.split(text)
        path = ROOT
        for eachPart in parts:
            if eachPart:
                path = path / eachPart
        return path

    FILE_NAME = re.compile("(.+)\\.([^\\.]+)$")
   
    def __init__(self, parent, name):
        self._container = parent
        self._name = name
        self._match = Path.FILE_NAME.match(name)
        
    def isRoot(self):
        return self._container is None

    def fullname(self):
        return self._name

    def basename(self):
        if not self.hasExtension():
            raise ValueError("No basename in '%s'" % self.fullname())
        return self._match.group(1)
        
    def extension(self):
        if not self.hasExtension():
            raise ValueError("No extension in '%s'" % self.fullname())
        return self._match.group(2)
    
    def hasExtension(self):
        return self._match and not self._match.group(2) is None

    def container(self):
        return self._container
    
    def parts(self):
        if self.isRoot():
            return []
        else:
            return self.container().parts() + [self.fullname()]
    
    def __contains__(self, other): 
        return self != other and self.__str__() in other.__str__()

    def __truediv__(self, other):
        return Path(self, other)

    def __repr__(self):
        return "%s/%s" % (self._container.__repr__(), self.fullname())
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self._name == other.fullname() and self._container == other._container

    def __hash__(self):
        return self.__str__().__hash__()
    
    
    
class Root(Path):
    
    def __init__(self):
        super().__init__(None, "root")

    def container(self):
        raise ValueError("The root directory has no container")

    def __repr__(self):
        return "/"
    
    def __eq__(self, other):
        return other.isRoot()

    def __hash__(self):
        return self._name.__hash__()


ROOT = Root()