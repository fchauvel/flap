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
from flap.path import Path
from flap.FileSystem import InMemoryFileSystem
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


class LatexProjectExtractionTests(TestCase):

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._directory = "home/"
        self._files = []

    def _create_files(self, *files):
        self._files = files
        for (path, content) in files:
            complete_path = Path.fromText(self._directory + path)
            self._file_system.create_file(complete_path, content)

    def _extract_project(self):
        root = self._file_system.open(Path.fromText(self._directory))
        return LatexProject.extract_from_directory(root)

    def _verify(self, project):
        assert len(self._files) > 0
        return self.assertListEqual([], self._expected().difference_with(project))

    def _do_test_with_files(self, *files):
        self._create_files(*files)
        project = self._extract_project()
        self._verify(project)

    def _expected(self):
        tex_files = []
        for (path, content) in self._files:
            tex_files.append(TexFile(path, content))
        return LatexProject(*tex_files)

    def test_extracting_a_simple_file(self):
        self._do_test_with_files(("main.tex", "content"))

    def test_extracting_a_two_files_project(self):
        self._do_test_with_files(
            ("main.tex", "content"),
            ("result.tex", "Here are some results"))

    def test_extracting_files_in_a_subdirectory(self):
        self._do_test_with_files(
            ("main.tex", "content"),
            ("test/result.tex", "Here are some results"))

    def test_extracting_a_complete_project(self):
        self._do_test_with_files(
            ("main.tex", "blablabla"),
            ("sections/introduction.tex", "Here are some results"),
            ("sections/development.tex", "Some more details"),
            ("sections/conclusions.tex", "Some more hindsight"),
            ("images/results.pdf", "PDF CONTENT"),
            ("images/sources/results.svg", "SVG CODE"),
            ("article.bib", "The bibliography"))

