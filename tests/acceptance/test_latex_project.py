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

from unittest import TestCase
from tests.acceptance.latex_project import LatexProject, TexFile, MissingFile, ExtraFile, DifferentContent


class TexFileTest(TestCase):

    def setUp(self):
        self.path = "test/main.tex"
        self.content = "foo"
        self.tex_file = TexFile(self.path, self.content)

    def test_name_is_exposed(self):
        self.assertEqual(self.path, self.tex_file.path)

    def test_content_is_exposed(self):
        self.assertEquals(self.content, self.tex_file.content)

    def test_equals_itself(self):
        self.assertEqual(self.tex_file, self.tex_file)

    def test_equals_a_similar_file(self):
        self.assertEqual(TexFile("test/main.tex", "foo"),
                         self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_path(self):
        self.assertNotEqual(TexFile("dir/" + self.path, self.content),
                            self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_content(self):
        self.assertNotEqual(TexFile(self.path, self.content + "blablabla"),
                            self.tex_file)


class LatexProjectTests(TestCase):

    def setUp(self):
        self.file = TexFile("main.tex", "blabla")
        self.tex = LatexProject(self.file)

    def test_files_is_exposed(self):
        self.assertEquals(self.file, self.tex.files["main.tex"])

    def test_equals_a_project_with_similar_files(self):
        self.assertEqual(LatexProject(TexFile("main.tex", "blabla")),
                         self.tex)

    def test_differ_when_file_content_differ(self):
        self.assertNotEqual(LatexProject(TexFile("main.tex", "THIS IS DIFFERENT!")),
                         self.tex)

    def test_differ_when_file_path_differ(self):
        self.assertNotEqual(LatexProject(TexFile("a/different/path.tex", "blabla")),
                         self.tex)

    def test_difference_with_itself(self):
        differences = self.tex.difference_with(self.tex)
        self.assertListEqual([], differences)

    def test_difference_with_a_project_with_an_missing_file(self):
        differences = self.tex.difference_with(LatexProject())
        self.assertListEqual([MissingFile(self.file)], differences)

    def test_difference_with_a_project_with_an_extra_file(self):
        extra_file = TexFile("extra/file.tex", "Extra blabla")
        differences = self.tex.difference_with(LatexProject(self.file, extra_file))
        self.assertListEqual([ExtraFile(extra_file)], differences)

    def test_difference_with_a_project_whose_file_content_differ(self):
        file = TexFile("main.tex", "something different!")
        differences = self.tex.difference_with(LatexProject(file))
        self.assertListEqual([DifferentContent(file)], differences)
