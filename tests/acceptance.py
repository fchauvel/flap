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

from tests.commons import LatexProject, FlapTest, TEST_DIRECTORY


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

    def test_copyAndRename(self):
        file = self.createAndOpenTestFile()

        copyPath = TEMP / "dir" / "copy.txt"
        self.fileSystem.copy(file, copyPath)
        

        copy = self.fileSystem.open(copyPath)
        self.assertEqual(copy.content(), self.content)


class AcceptanceTest(FlapTest):

    def setUp(self):
        super().setUp()
        self.file_system = OSFileSystem()
        self.prepareLatexProject()

    def prepareLatexProject(self):
        self.project.root_latex_code = \
            "\\documentclass{article}\n" \
            "\\includeonly{partB/main}\n" \
            "\\begin{document}\n" \
            "   \\subfile{partA}\n" \
            "   \\include{partB/main}\n" \
            "\\end{document}"

        self.project.parts["partA.tex"] = \
            "\\documentclass[../main.tex]{subfiles}\n" \
            "\\begin{document}\n" \
            "   \\input{result}\n" \
            "\\end{document}\n"

        self.project.parts["result.tex"] = \
            "\\includegraphics% This is a multi-lines command\n" \
            "[width=\\textwidth]%\n" \
            "{plot}"

        self.project.parts["partB/main.tex"] = "blablah"

        self.project.images = ["plot.pdf"]

        self.project.resources = ["style.sty", "test.cls" ]

    def run_flap(self, project):
        root = self.file_system.forOS(project.root_latex_file)
        output = self.file_system.forOS(self.output_directory)
        main(["-v", root, output])

    def tearDown(self):
        self.file_system.deleteDirectory(TEST_DIRECTORY)

    def run_test(self):
        self.project.create_on(self.file_system)

        self.run_flap(self.project)

        self.verify_merge("\\documentclass{article}\n"
                          "\n"
                          "\\begin{document}\n"
                          "   \n"
                          "   \\includegraphics[width=\\textwidth]{plot}\n"
                          "\n"
                          "\n"
                          "   blablah\\clearpage \n"
                          "\\end{document}")

        self.verify_images()
        self.verify_resources()

    def test_flatten_latex_project(self):
        self.run_test()

    def test_flatten_latex_project_locally(self):
        self.working_directory = self.project.directory
        self.run_test()

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
