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

import os

from flap.util.path import Path, ROOT


class File:
   
    def __init__(self, file_system, path, content):
        assert path, "Invalid path (found '%s')" % path.full()
        self.fileSystem = file_system
        self._path = path
        self._content = content
    
    def is_file(self):
        return True
    
    def is_directory(self):
        return not self.is_file()

    @classmethod
    def exists(cls):
        return True
    
    def is_missing(self):
        return not self.exists()
    
    def contains(self, content):
        return self._content == content
    
    def content(self):
        if not self._content:
            self._content = self.fileSystem.load(self._path)
        return self._content

    def path(self):
        return self._path
    
    def fullname(self):
        return self._path.fullname()
    
    def basename(self):
        return self._path.basename()
    
    def has_extension(self, extension=None):
        return self._path.has_extension(extension)

    def has_extension_from(self, candidates_extensions):
        for any_extension in candidates_extensions:
            if self._path.has_extension(any_extension):
                return True

    def extension(self):
        return self._path.extension()
    
    def container(self):
        return self.fileSystem.open(self._path.container())
        
    def sibling(self, name):
        return self.fileSystem.open(self._path.container() / name) 

    @classmethod
    def files(cls):
        return []
    
    def files_that_matches(self, pattern):
        path = Path.fromText(str(self._path) + "/" + str(pattern))
        directory = self.fileSystem.open(path.container())
        return [ any_file for any_file in directory.files() if str(any_file.path()).startswith(str(path)) ]

    def __repr__(self):
        return str(self.path())
    
    
class Directory(File):
    
    def __init__(self, file_system, path):
        super().__init__(file_system, path, None)
             
    def is_file(self):
        return False
    
    def content(self):
        return None 
            
    def files(self):
        return self.fileSystem.filesIn(self.path())
     
    
class MissingFile(File):
    
    def __init__(self, path):
        super().__init__(None, path, None)
        
    def exists(self):
        return False
    
    def contains(self, content):
        return False
    
    def content(self):
        return None
    
    def location(self):
        return None


class FileSystem:
    
    def create_file(self, path, content):
        pass
    
    def createDirectory(self, path):
        pass

    def deleteDirectory(self, path):
        pass
    
    def open(self, path):
        pass
    
    def filesIn(self, path):
        pass
    
    def copy(self, file, destination):
        pass
    
    def load(self, path):
        pass

    def move_to_directory(self, path):
        pass


class OSFileSystem(FileSystem):
    
    def __init__(self):
        super().__init__()
        self.current_directory = Path.fromText(os.getcwd())

    @staticmethod
    def for_OS(path):
        return os.path.sep.join([eachPart.fullname() for eachPart in path.parts()])

    def move_to_directory(self, path):
        os.chdir(self.for_OS(path))
        
    def create_file(self, path, content):
        self._create_path(path)
        os_path = self.for_OS(path)
        with open(os_path, "w") as f:
            f.write(content)
        
    def deleteDirectory(self, path):
        import shutil
        osPath = self.for_OS(path)
        if os.path.exists(osPath):
            shutil.rmtree(osPath)
    
    def open(self, path):
        osPath = self.for_OS(path)
        if os.path.isdir(osPath):
            return Directory(self, path)
        else:
            return File(self, path, None)

    def filesIn(self, path):
        return [self.open(path / each) for each in os.listdir(self.for_OS(path))]

    def copy(self, file, destination):
        import shutil

        self._create_path(destination)
        
        source = self.for_OS(file.path())
        target = destination if destination.has_extension() else destination / file.fullname()

        shutil.copyfile(source, self.for_OS(target))

    def _create_path(self, path):
        targetDir = path
        if path.has_extension():
            targetDir = path.container()

        os_target = self.for_OS(targetDir)
        if not os.path.exists(os_target):
            os.makedirs(os_target) 
        
    def load(self, path):
        assert path, "Invalid path (found '%s')" % path
        os_path = self.for_OS(path)
        with open(os_path) as file:
            return file.read()


class InMemoryFileSystem(FileSystem):
        
    def __init__(self, pathSeparator = os.path.sep):
        super().__init__()
        self.drive = {}
        self._current_directory = ROOT
        self.pathSeparator = pathSeparator

    def move_to_directory(self, path):
        self._current_directory = path.absolute_from(self._current_directory)

    def createDirectory(self, path):
        if path in self.drive.keys():
            if self.drive[path].is_file():
                raise ValueError("There is already a resource at '%s'" % path.full())
        self.drive[path] = Directory(self, path)
        if not path.isRoot():
            self.createDirectory(path.container())

    def create_file(self, path, content):
        if not isinstance(content, str):
            raise ValueError("File content should be text!")
        absolute = path.absolute_from(self._current_directory)
        self.drive[absolute] = File(self, absolute, content)
        self.createDirectory(absolute.container())
        
    def filesIn(self, path):
        return [ self.drive[p] for p in self.drive.keys() if p in path and len(p.parts()) == len(path.parts()) + 1 ]
        
    def open(self, path):
        absolute = path.absolute_from(self._current_directory)
        if absolute in self.drive.keys():
            return self.drive[absolute]
        else:
            return MissingFile(absolute)

    def copy(self, file, destination):
        if destination.has_extension():
            path = destination
        else:
            path = destination / file.path().fullname()
        absolute = path.absolute_from(self._current_directory)
        self.drive[absolute] = File(self, absolute, file.content())

