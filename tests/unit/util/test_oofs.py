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

from flap.util.oofs import InMemoryFileSystem
from flap.util.path import Path, ROOT


class InMemoryFileSystemTest(unittest.TestCase):

    def setUp(self):
        self.fileSystem = InMemoryFileSystem()
        self.current_directory = Path.fromText("/temp")

    def test_file_creation(self):
        path = Path.fromText("dir/test/source.tex")
        self.fileSystem.create_file(path, "blah")

        file = self.fileSystem.open(Path.fromText("dir/test/source.tex"))

        self.assertTrue(file.exists())
        self.assertTrue(file.contains("blah"))

    def test_create_file_rejects_content_that_is_not_text(self):
        path = Path.fromText("dir/test.txt")
        with self.assertRaises(ValueError):
            self.fileSystem.create_file(path, [1, 2, 3, 4])

    def testThatMissingFileDoNotExist(self):
        path = Path.fromText("file\\that\\do\\not\\exist.txt")
        file = self.fileSystem.open(path)
        self.assertFalse(file.exists())

    def testContainingDirectoryIsAvailable(self):
        path = Path.fromText("my\\dir\\test.txt")
        self.fileSystem.create_file(path, "data")
        file = self.fileSystem.open(path)
        self.assertEqual(file.container().path(), ROOT / "my" / "dir")

    def testFullNameIsAvailable(self):
        path = Path.fromText("/my/dir/test.txt")
        self.fileSystem.create_file(path, "data")
        file = self.fileSystem.open(path)
        self.assertEqual(file.fullname(), "test.txt")

    def testBasenameIsAvailable(self):
        path = Path.fromText("my/dir/test.txt")
        self.fileSystem.create_file(path, "whatever")
        file = self.fileSystem.open(path)
        self.assertEqual(file.basename(), "test")

    def testDirectoryContainsFiles(self):
        self.fileSystem.create_file(Path.fromText("dir/test.txt"), "x")
        self.fileSystem.create_file(Path.fromText("dir/test2.txt"), "y")
        file = self.fileSystem.open(Path.fromText("dir"))
        self.assertEqual(len(file.files()), 2)

    def testDirectoryContainsOnlyItsDirectContent(self):
        self.fileSystem.create_file(Path.fromText("dir/test.txt"), "x")
        self.fileSystem.create_file(Path.fromText("dir/test2.txt"), "y")
        self.fileSystem.create_file(Path.fromText("dir/more/test.txt"), "x")
        directory = self.fileSystem.open(Path.fromText("dir"))
        self.assertEqual(len(directory.files()), 3, [
                         str(file.path()) for file in directory.files()])

    def testFilteringFilesInDirectory(self):
        self.fileSystem.create_file(Path.fromText("dir/test.txt"), "x")
        self.fileSystem.create_file(Path.fromText("dir/test2.txt"), "y")
        self.fileSystem.create_file(Path.fromText("dir/blah"), "z")
        file = self.fileSystem.open(Path.fromText("dir"))
        self.assertEqual(len(file.files_that_matches("test")), 1)

    def testCopyingFile(self):
        source = Path.fromText("dir/test.txt")
        self.fileSystem.create_file(source, "whatever")
        file = self.fileSystem.open(source)
        destination = Path.fromText("dir2/clone")

        self.fileSystem.copy(file, destination)

        copy = self.fileSystem.open(destination / "test.txt")
        self.assertTrue(copy.exists())
        self.assertEqual(copy.content(), "whatever")

    def test_copy_while_renaming(self):
        source = Path.fromText("dir/test.txt")
        self.fileSystem.create_file(source, "whatever")

        file = self.fileSystem.open(source)

        destination = Path.fromText("dir2/clone/test_copy.txt")
        self.fileSystem.copy(file, destination)

        copy = self.fileSystem.open(destination)
        self.assertTrue(copy.exists())
        self.assertEqual(copy.content(), "whatever")

    def test_files_that_match(self):
        self.fileSystem.create_file(Path.fromText("dir/foo/bar/test.txt"), "x")
        directory = self.fileSystem.open(Path.fromText("dir/foo"))
        results = directory.files_that_matches("bar/test")
        self.assertEqual(len(results), 1)

    def test_files_that_match_with_multiple_matches(self):
        self.fileSystem.create_file(Path.fromText("dir/foo/test.txt"), "x")
        self.fileSystem.create_file(Path.fromText("dir/foo/subtest.txt"), "x")
        directory = self.fileSystem.open(Path.fromText("dir/foo"))
        results = directory.files_that_matches("test")
        self.assertEqual(len(results), 1)

    def test_finding_files_in_the_current_directory(self):
        path = Path.fromText("/root/foo/bar/test.txt")
        self.fileSystem.create_file(path, "blahblah blah")

        self.fileSystem.move_to_directory(Path.fromText("/root/foo"))
        file = self.fileSystem.open(Path.fromText("bar/test.txt"))

        self.assertEqual(file.content(), "blahblah blah")


if __name__ == "__main__":
    unittest.main()
