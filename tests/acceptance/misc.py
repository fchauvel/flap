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

from flap.ui import UI
from flap.util.oofs import OSFileSystem
from flap.util.path import Path, TEMP
from io import StringIO

from re import search
from tests.commons import FlapTest, AcceptanceTestRunner
from tests.latex_project import a_project


class OSFileSystemTest(TestCase):
    
    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.path = TEMP / "flap_os" / "test.txt"
        self.content = "blahblah blah"

        self.fileSystem.deleteDirectory(TEMP / "flap_os")
        self.fileSystem.deleteDirectory(TEMP / "flatexer_copy")
    
    def createAndOpenTestFile(self):
        self.fileSystem.create_file(self.path, self.content)
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

        copy_path = TEMP / "dir" / "copy.txt"
        self.fileSystem.copy(file, copy_path)

        copy = self.fileSystem.open(copy_path)
        self.assertEqual(copy.content(), self.content)


class MoreAcceptanceTests(FlapTest):

    def setUp(self):
        super().setUp()
        self._display = StringIO()
        self._runner = AcceptanceTestRunner(self._file_system, TEMP / "flap" , UI(self._display))
        self._assume = a_project()\
            .with_main_file(r"\documentclass{article}"
                            r"\begin{document}"
                            r"   This is a \LaTeX document!"
                            r"\end{document}")
        self._expect = a_project()\
            .with_merged_file(r"\documentclass{article}"
                              r"\begin{document}"
                              r"   This is a \LaTeX document!"
                              r"\end{document}")

    def _verify_no_error_in_output(self):
        output = self._display.getvalue()
        self.assertFalse(search(r"Error:", output), output)

    def test_basic_case(self):
        self._do_test_and_verify()
        self._verify_no_error_in_output()

    def test_invoking_locally(self):
        self._runner._root_file = lambda name: Path.fromText("main.tex")

        self._do_test_and_verify()
        self._verify_no_error_in_output()

    def test_usage_is_shown(self):
        self._runner._arguments = lambda name: []

        self._runner._run_flap("whatever")

        output = self._display.getvalue()
        self.assertNotEqual("", output, "No output detected")
        self.assertTrue(search(r"Usage\:", output), output)
        self.assertTrue(search(r"python -m flap <path/to/tex_file> <output/directory>", output), output)




if __name__ == "__main__":
    testmain()
