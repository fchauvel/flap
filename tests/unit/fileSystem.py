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

import unittest

from flap.FileSystem import InMemoryFileSystem
from flap.path import Path, ROOT


class InMemoryFileSystemTest(unittest.TestCase):

    def setUp(self):
        self.fileSystem = InMemoryFileSystem() 
       
    def testThatCreatedFilesExist(self):
        path = Path.fromText("source.tex")
        self.fileSystem.createFile(path, "blah")
        
        file = self.fileSystem.open(path)
        
        self.assertTrue(file.exists())
        self.assertTrue(file.contains("blah"))


    def testThatMissingFileDoNotExist(self):
        path = Path.fromText("file\\that\\do\\not\\exist.txt")
        
        file = self.fileSystem.open(path)
        
        self.assertFalse(file.exists())


    def testContainingDirectoryIsAvailable(self):
        path = Path.fromText("my\\dir\\test.txt")
        self.fileSystem.createFile(path, "data")
        
        file = self.fileSystem.open(path) 
        
        self.assertEqual(file.container().path(), ROOT / "my" / "dir")
        
        
    def testFullNameIsAvailable(self):
        path = Path.fromText("/my/dir/test.txt")

        self.fileSystem.createFile(path, "data")
        
        file = self.fileSystem.open(path)
        
        self.assertEqual(file.fullname(), "test.txt")
        
        
    def testBasenameIsAvailable(self):
        path = Path.fromText("my/dir/test.txt")
        self.fileSystem.createFile(path, "whatever")

        file = self.fileSystem.open(path)
        
        self.assertEqual(file.basename(), "test")
        
        
    def testDirectoryContainsFiles(self):
        self.fileSystem.createFile(Path.fromText("dir/test.txt"), "x")
        self.fileSystem.createFile(Path.fromText("dir/test2.txt"), "y")
        
        file = self.fileSystem.open(Path.fromText("dir"))
        
        self.assertEqual(len(file.files()), 2)
        
        
    def testFilteringFilesInDirectory(self):
        self.fileSystem.createFile(Path.fromText("dir/test.txt"), "x")
        self.fileSystem.createFile(Path.fromText("dir/test2.txt"), "y")
        self.fileSystem.createFile(Path.fromText("dir/blah"), "z")
        
        file = self.fileSystem.open(Path.fromText("dir"))
        
        self.assertEqual(len(file.filesThatMatches("test")), 2)
        
        
    def testCopyingFile(self):
        source = Path.fromText("dir/test.txt")
        self.fileSystem.createFile(source, "whatever")
        
        file = self.fileSystem.open(source)
        
        destination = Path.fromText("dir2/clone")
        self.fileSystem.copy(file, destination)
        
        copy = self.fileSystem.open(destination / "test.txt")
        self.assertTrue(copy.exists())
        self.assertEqual(copy.content(), "whatever")
        
        
if __name__ == "__main__":
    unittest.main()