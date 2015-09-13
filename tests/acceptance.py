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
from flap.ui import main
from flap.FileSystem import OSFileSystem
from flap.path import TEMP

from tests.commons import LatexProjectBuilder, FlapRunner, FlapVerifier


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