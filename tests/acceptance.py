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

from tests.commons import LatexProject, FlapRunner, FlapVerifier


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
        self.project = self.prepareLatexProject()
        self._runner = FlapRunner(self._file_system, TEMP, TEMP / "output")
        self._verify = FlapVerifier(self.project, self._runner)

    def prepareLatexProject(self):
        project = LatexProject()
        project.root_latex_code = "\\documentclass{article}\n" \
                                       "\\graphicspath{images}\n" \
                                       "\\includeonly{partA,partB}" \
                                       "\\begin{document}\n" \
                                       "    \\include{partA}\n" \
                                       "    \\include{partB}\n" \
                                       "\\end{document}"

        project.parts["partA.tex"] = "\\input{result}"
        project.parts["result.tex"] = "\\includegraphics{plot}"
        project.parts["partB.tex"] = "blablah"

        project.images = ["plot.pdf"]

        project.resources = ["style.sty", "test.cls" ]
        return project

    def tearDown(self):
        self._file_system.move_to_directory(TEMP)

    def run_test(self):
        self.project.create_on(self._file_system)

        self._runner.run_flap(self.project)

        self._verify.merged_content_is("\documentclass{article}\n"
                                       "\n"
                                       "\\begin{document}\n"
                                       "    \\includegraphics{plot}\\clearpage \n"
                                       "    blablah\\clearpage \n"
                                       "\\end{document}")
        self._verify.resources()

    def test_flatten_latex_project(self):
        self.run_test()

    def test_flatten_latex_project_locally(self):
        self._runner.working_directory = self.project.directory
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