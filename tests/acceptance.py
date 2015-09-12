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


class AcceptanceTest(TestCase):

    def setUp(self):
        self.configure()
        self.clear_working_directory()
        self.create_root_latex_file()
        self.create_latex_part_A()
        self.create_latex_part_B()
        self.create_image()
        self.create_latex_resources()

    def configure(self):
        self.fileSystem = OSFileSystem()
        self.workingDir = TEMP / "flap"
        self.source = self.workingDir / "project"
        self.output = self.workingDir / "output"

    def clear_working_directory(self):
        self.fileSystem.deleteDirectory(self.workingDir)

    def create_root_latex_file(self):
        latex_code = "\documentclass{article}\n" \
                     "\\graphicspath{images}\n" \
                     "\\includeonly{partA,partB}" \
                     "\\begin{document}\n" \
                     "    \\include{partA}\n" \
                     "    \\include{partB}\n" \
                     "\\end{document}"
        self.fileSystem.createFile(self.source / "main.tex", latex_code)

    def create_latex_part_A(self):
        self.fileSystem.createFile(self.source / "partA.tex", "\\input{result}")
        self.fileSystem.createFile(self.source / "result.tex", "\\includegraphics{plot}")

    def create_latex_part_B(self):
        self.fileSystem.createFile(self.source / "partB.tex", "blablah")

    def create_latex_resources(self):
        self.fileSystem.createFile(self.source / "style.sty", "some style crap")
        self.fileSystem.createFile(self.workingDir / "test.cls", "a LaTeX class")
        symlink(self.fileSystem.forOS(self.workingDir / "test.cls"), self.fileSystem.forOS(self.source / "test.cls"))

    def create_image(self):
        self.fileSystem.createFile(self.source / "images" / "plot.pdf", "image")

    def tearDown(self):
        self.fileSystem.move_to_directory(TEMP)

    def verify_merge_sources(self, file):
        expected_content = "\documentclass{article}\n" \
                           "\n" \
                           "\\begin{document}\n" \
                           "    \\includegraphics{plot}\\clearpage \n" \
                           "    blablah\\clearpage \n" \
                           "\\end{document}"
        self.assertEqual(file.content(), expected_content)

    def test_flatten_latex_project(self):
        root = self.fileSystem.forOS(TEMP / "flap" / "project" / "main.tex")
        output = self.fileSystem.forOS(TEMP / "flap" / "output")

        print(root)
        main(["-v", root, output])
        
        file = self.fileSystem.open(self.output / "merged.tex")
        self.verify_merge_sources(file)

        styFile = self.fileSystem.open(self.output / "style.sty")
        self.assertEqual(styFile.content(), "some style crap")

    def test_flatten_latex_project_locally(self):
        output = self.fileSystem.forOS(TEMP / "flap" / "output")

        self.fileSystem.move_to_directory(TEMP / "flap" / "project")
        main(["-v", "main.tex", output])

        file = self.fileSystem.open(self.output / "merged.tex")
        self.verify_merge_sources(file)

        style = self.fileSystem.open(self.output / "style.sty")
        self.assertEqual(style.content(), "some style crap")

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