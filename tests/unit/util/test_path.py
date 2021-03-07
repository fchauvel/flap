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

from flap.util.path import Path, ROOT, TEMP, CURRENT_DIRECTORY
from tempfile import gettempdir


class PathTests(unittest.TestCase):

    def testTemp(self):
        path = TEMP
        self.assertTrue(path.fullname() in gettempdir())

    def test_path_to_file(self):
        path = (ROOT / "test" / "source.tex")
        self.assertEqual(path.container(), ROOT / "test")
        self.assertEqual(path.fullname(), "source.tex")

    def test_appending_a_path(self):
        path1 = ROOT / "dir/test"
        path2 = ROOT / "dir" / "test"

        self.assertEqual(path1, path2)

    def test_appending_a_path_that_ends_with_a_slash(self):
        path1 = ROOT / "dir/test/"
        path2 = ROOT / "dir" / "test"

        self.assertEqual(path1, path2)

    def test_appending_a_path_that_starts_with_a_dot(self):
        path1 = ROOT / "./dir/test/"
        path2 = ROOT / "dir" / "test"

        self.assertEqual(path1, path2)

    def test_has_extension(self):
        path = ROOT / "source.tex"

        self.assertTrue(path.has_extension())

    def test_basename(self):
        path = ROOT / "source.tex"

        self.assertEqual(path.basename(), "source")

    def test_as_absolute_with_current(self):
        path = Path.fromText("./test/foo.txt")

        absolute_path = path.absolute_from(Path.fromText("/home/franck"))

        self.assertEqual(absolute_path,
                         Path.fromText("/home/franck/test/foo.txt"))

    def test_as_absolute_with_implicit_current(self):
        path = Path.fromText("test/foo.txt")

        absolute_path = path.absolute_from(Path.fromText("/home/franck"))

        self.assertEqual(absolute_path,
                         Path.fromText("/home/franck/test/foo.txt"))

    def test_as_absolute_with_parent(self):
        path = Path.fromText("../test/foo.txt")

        absolute_path = path.absolute_from(Path.fromText("/home/franck"))

        self.assertEqual(absolute_path, Path.fromText("/home/test/foo.txt"))

    def test_as_absolute_with_absolute_path(self):
        path = Path.fromText("/home/test/foo.txt")

        absolute_path = path.absolute_from(Path.fromText("/home/franck"))

        self.assertEqual(absolute_path, Path.fromText("/home/test/foo.txt"))

    def test_as_absolute_with_root(self):
        path = ROOT

        absolute_path = path.absolute_from(Path.fromText("/home/franck"))

        self.assertEqual(absolute_path, ROOT)

    def test_relative_to_directory(self):
        path = Path.fromText("/home/test/foo.txt")

        relative = path.relative_to(Path.fromText("/home"))

        self.assertEqual(relative, Path.fromText("test/foo.txt"))

    def test_relative_to_file(self):
        path = Path.fromText("/home/test/foo.txt")

        relative = path.relative_to(Path.fromText("/home/test"))

        self.assertEqual(relative, Path.fromText("foo.txt"))

    def test_without_extension(self):
        path = Path.fromText("/home/test/foo.txt")

        self.assertEqual(path.without_extension(),
                         Path.fromText("/home/test/foo"))

    def test_container(self):
        path = ROOT / "foo.tex"
        self.assertEqual(ROOT, path.container())

    def test_empty_container(self):
        path = Path.fromText("foo.tex")
        self.assertEqual(CURRENT_DIRECTORY, path.container())

    def testContainment(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir"

        self.assertTrue(path1 in path2)

    def testContainmentUnderEquality(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir" / "file.txt"

        self.assertFalse(path1 in path2)
        self.assertFalse(path2 in path1)

    def testPathBuilding(self):
        path = Path.fromText("\\Users\\franckc\\file.txt")

        self.assertEqual(path, ROOT / "Users" / "franckc" / "file.txt")

    def test_parsing_directory(self):
        path = Path.fromText("project/img/")

        parts = [each.fullname() for each in path.parts()]
        self.assertEqual(parts, ["project", "img"], "Wrong parts!")

    def testParts(self):
        path = Path.fromText("C:\\Users\\franckc\\pub\\JOCC\\main.tex")

        self.verify_parts(path, ["C:", "Users", "franckc", "pub",
                                 "JOCC", "main.tex"])

    def verify_parts(self, path, expectedParts, ):
        parts = [each.fullname() for each in path.parts()]
        self.assertEqual(parts, expectedParts)

    def testPathWithNewlines(self):
        path = Path.fromText("/Root/Foo\nBar\nBaz/home")
        self.verify_parts(path, ["", "Root", "FooBarBaz", "home"])

    def test_remove_trailing_spaces(self):
        path = Path.fromText("/text/ blabla /test.txt")
        self.assertEqual(path, Path.fromText("/text/blabla/test.txt"))

    def test_is_absolute_on_unix_paths(self):
        path = Path.fromText("/home/franck/test.tex")
        self.assertTrue(path.is_absolute())

    def test_is_absolute_on_windows_paths(self):
        path = Path.fromText("C:\\Users\\franckc\\file.txt")
        self.assertTrue(path.is_absolute())

    def test_is_absolute_with_relative(self):
        path = Path.fromText("franck/test.tex")
        self.assertFalse(path.is_absolute())

if __name__ == "__main__":
    unittest.main()
