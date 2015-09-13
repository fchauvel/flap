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

from unittest import TestCase, main as testmain

from mock import patch
from io import StringIO
from re import search
from os import symlink
from flap.ui import main
from flap.FileSystem import OSFileSystem
from flap.path import TEMP


class OSFileSystemTest(TestCase):
    
    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.path = TEMP / "flap" / "test.txt"
        self.content = "blahblah blah"

        self.fileSystem.deleteDirectory(TEMP / "flap")
        self.fileSystem.deleteDirectory(TEMP / "flatexer_copy")
    
    def createAndOpenTestFile(self):
        self.fileSystem.createFile(self.path, self.content)
        return self.fileSystem.open(self.path)
    
    def testCreateAndOpenFile(self):
        file = self.createAndOpenTestFile()
        
        self.assertEqual(file.content(), self.content)

    def testCopyAndOpenFile(self):
        file = self.createAndOpenTestFile()
        
        copyPath = TEMP / "flatexer_copy"
        
        self.fileSystem.copy(file, copyPath)
        copy = self.fileSystem.open(copyPath / "test.txt")
        
        self.assertEqual(copy.content(), self.content)


class LatexProjectBuilder:
    """
    Helps build the file structure of a LaTeX project.
    It does not contain any test, but it uses assertions
    """

    IMAGE_CONTENT = "image data"
    STYLE_CONTENT = "some style definitions"
    CLASS_CONTENT = "a class definition"

    def __init__(self, file_system):
        self._file_system = file_system
        self.directory = TEMP / "project"
        self.main_latex_file = "main.tex"
        self.images_directory = "images"

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, path):
        self._directory = path

    @property
    def main_latex_file(self):
        return self._main_latex_file

    @main_latex_file.setter
    def main_latex_file(self, path):
        self._main_latex_file = self._directory / path

    @property
    def images_directory(self):
        return self._images_directory

    @images_directory.setter
    def images_directory(self, path):
        self._images_directory = self._directory / path

    def clear(self):
        self._file_system.deleteDirectory(self._directory)

    def create_root_latex_file(self, content):
        self._file_system.createFile(self._main_latex_file, content)

    def create_latex_file(self, path, content):
        self._file_system.createFile(self._directory / path, content)

    def create_image(self, path):
        self._file_system.createFile(self._images_directory / path, LatexProjectBuilder.IMAGE_CONTENT)

    def create_style_file(self, path):
        self._file_system.createFile(self._directory / path, LatexProjectBuilder.STYLE_CONTENT)

    def create_class_file(self, path):
        self._file_system.createFile(path, "a class definition")

    def create_symbolic_link(self, link_path, link_target):
        symlink(self._file_system.forOS(link_target), self._file_system.forOS(self._directory / link_path))

    @property
    def path_to_root_latex_file(self):
        return self._file_system.forOS(self._main_latex_file)


class FlapRunner:
    """
    Invoke FLaP, and provides access to the outputted files
    """

    def __init__(self, latex_project, working_directory, output_directory):
        self._project = latex_project
        self.working_directory = working_directory
        self.output_directory = output_directory
        self.merged_file = "merged.tex"

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, path):
        self._working_directory = path

    @property
    def output_directory(self):
        return self._output_directory

    @output_directory.setter
    def output_directory(self, directory):
        self._output_directory = directory

    @property
    def merged_file(self):
        return self._merged_file

    @merged_file.setter
    def merged_file(self, path):
        self._merged_file = self.output_directory / path

    def run_flap(self):
        root = self._project.path_to_root_latex_file
        output = self._project._file_system.forOS(self.output_directory)
        main(["-v", root, output])

    def output_file(self, path):
        return self.output_directory / path


class FlapVerifier(TestCase):
    """
    Verify the outputs produced by FLaP
    """

    def __init__(self, file_system, runner):
        super().__init__()
        self._file_system = file_system
        self._runner = runner

    def merged_content_is(self, expected):
        self.assertEqual(self.merged_content(), expected)

    def style_file(self, path):
        self.assertEqual(self.content_of(self._runner.output_file(path)), LatexProjectBuilder.STYLE_CONTENT)

    def class_file(self, path):
        self.assertEqual(self.content_of(self._runner.output_file(path)), LatexProjectBuilder.CLASS_CONTENT)

    def merged_content(self):
        return self.content_of(self._runner.merged_file)

    def content_of(self, path):
        return self._file_system.open(path).content()


class AcceptanceTest(TestCase):

    def setUp(self):
        self._file_system = OSFileSystem()
        self._builder = LatexProjectBuilder(self._file_system)
        self._runner = FlapRunner(self._builder, TEMP, TEMP / "output")
        self._verify = FlapVerifier(self._file_system, self._runner)
        self._builder.clear()

        self._builder.create_root_latex_file(   "\\documentclass{article}\n"
                                                "\\graphicspath{images}\n"
                                                "\\includeonly{partA,partB}"
                                                "\\begin{document}\n"
                                                "    \\include{partA}\n"
                                                "    \\include{partB}\n"
                                                "\\end{document}")

        self._builder.create_latex_file("partA.tex", "\\input{result}")

        self._builder.create_latex_file("result.tex", "\\includegraphics{plot}")

        self._builder.create_latex_file("partB.tex", "blablah")

        self._builder.create_image("plot.pdf")

        self._builder.create_style_file("style.sty")

        self._builder.create_class_file(TEMP / "test.cls")

        self._builder.create_symbolic_link("test.cls",  TEMP / "test.cls")

    def tearDown(self):
        self._file_system.move_to_directory(TEMP)

    def verify_merge_sources(self):
        expected = "\documentclass{article}\n" \
                           "\n" \
                           "\\begin{document}\n" \
                           "    \\includegraphics{plot}\\clearpage \n" \
                           "    blablah\\clearpage \n" \
                           "\\end{document}"
        self._verify.merged_content_is(expected)

    def test_flatten_latex_project(self):
        self._runner.run_flap()

        self.verify_merge_sources()
        self._verify.style_file("style.sty")
        self._verify.class_file("test.cls")

    def test_flatten_latex_project_locally(self):
        self._runner.working_directory = self._builder.directory

        self._runner.run_flap()

        self.verify_merge_sources()
        self._verify.style_file("style.sty")
        self._verify.class_file("test.cls")


    def test_usage_is_shown(self):
        mock = StringIO()
        def patched_show(message):
            mock.write(message)
        with patch("flap.ui.UI._show", side_effect=patched_show):
            main([])
        output = mock.getvalue()
        self.assertNotEqual("", output, "No output detected")
        self.assertTrue(search(r"Usage\:", output), output)
        self.assertTrue(search(r"python -m flap <path/to/tex_file> <output/directory>", output), output)


if __name__ == "__main__":
    testmain()