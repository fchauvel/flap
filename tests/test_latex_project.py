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

from flap.util.oofs import InMemoryFileSystem
from flap.util.path import Path
from tests.latex_project import Fragment, LatexProject, LatexProjectBuilder, TexFile, a_project


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
        self.tex.assert_is_equivalent_to(self.tex)

    def test_difference_with_a_project_with_an_missing_file(self):
        try:
            self.tex.assert_is_equivalent_to(LatexProject())
            self.fail("Exception expected")

        except AssertionError as error:
            self.assertEqual(LatexProject.MISSING_FILE.format(file="main.tex"),
                             str(error))

    def test_difference_with_a_project_with_an_extra_file(self):
        try:
            extra_file = TexFile("extra/file.tex", "Extra blabla")
            self.tex.assert_is_equivalent_to(LatexProject(self.file, extra_file))
            self.fail("Exception expected")

        except AssertionError as error:
            self.assertEqual(LatexProject.UNEXPECTED_FILE.format(file=extra_file.path),
                             str(error))

    def test_difference_with_a_project_whose_file_content_differs(self):
        try:
            content = "something different"
            self.tex.assert_is_equivalent_to(LatexProject(TexFile("main.tex", content)))
            self.fail("Exception expected")

        except AssertionError as error:
            self.assertEqual(LatexProject.CONTENT_MISMATCH.format(file="main.tex", expected="blabla", actual=content),
                             str(error))


class LatexProjectGenerationTests(TestCase):

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._directory = "home"

    def test_setup_a_single_file_project(self):
        self._do_test_setup(
            LatexProject(TexFile("main.tex", "blabla"))
        )

    def test_setup_a_two_files_project(self):
        self._do_test_setup(LatexProject(
            TexFile("main.tex", "blabla"),
            TexFile("result.tex", "Some results"))
        )

    def test_setup_a_project_with_subdirectories(self):
        self._do_test_setup(LatexProject(
            TexFile("main.tex", "blabla"),
            TexFile("sections/introduction.tex", "introduction"),
            TexFile("sections/conclusions.tex", "conclusions"),
            TexFile("images/results.pdf", "PDF"))
        )

    def _do_test_setup(self, project):
        project.setup(self._file_system, Path.fromText(self._directory))
        self._verify(project)

    def _verify(self, project):
        for (path, file) in project.files.items():
            file_on_disk = self._file_system.open(Path.fromText(self._directory) / path)
            self.assertEqual(file.content, file_on_disk.content())


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
        self._expected().assert_is_equivalent_to(project)

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


class BuilderTests(TestCase):

    def test_build_empty_project(self):
        project = a_project().build()

        self.assertEqual(LatexProject(), project)

    def test_build_single_file_projects(self):
        project = a_project()\
            .with_file("main.tex", "foo")\
            .build()
        self.assertEqual(LatexProject(TexFile("main.tex", "foo")), project)

    def test_build_a_main_file_project(self):
        project = a_project()\
            .with_main_file("foo")\
            .build()
        self.assertEqual(LatexProject(TexFile(LatexProjectBuilder.MAIN_FILE, "foo")), project)

    def test_build_a_merged_file_project(self):
        project = a_project()\
            .with_merged_file("foo")\
            .build()
        self.assertEqual(LatexProject(TexFile(LatexProjectBuilder.MERGED_FILE, "foo")), project)

    def test_build_project_with_image(self):
        project = a_project()\
            .with_image("img/result.pdf")\
            .build()
        self.assertEqual(
            LatexProject(TexFile("img/result.pdf", LatexProjectBuilder.IMAGE_CONTENT.format(key="img_result.pdf"))),
            project)


class FragmentTest(TestCase):

    def setUp(self):
        self._file = "test.tex"
        self._line = 1
        self._column = 2
        self._code = r"\input{file.tex}"

    def test_conversion_to_dictionary(self):
        fragment = Fragment(self._file, self._line, self._column, self._code)
        expected = {Fragment.KEY_FILE: self._file,
                    Fragment.KEY_LINE: self._line,
                    Fragment.KEY_COLUMN : self._column,
                    Fragment.KEY_CODE: self._code}
        self.assertEqual(expected, fragment.as_dictionary)