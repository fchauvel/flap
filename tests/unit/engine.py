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

from unittest import TestCase, main

from flap.engine import Flap, Fragment, Listener
from flap.substitutions.factory import ProcessorFactory
from flap.util.oofs import InMemoryFileSystem, File, MissingFile
from flap.util.path import ROOT
from mock import MagicMock
from tests.commons import FlapTest


class FragmentTest(TestCase):
    """
    Specification of the Fragment class 
    """

    def setUp(self):
        self.file = File(None, ROOT / "main.tex", "xxx")
        self.fragment = Fragment(self.file, 13, "blah blah")

    def testShouldExposeLineNumber(self):
        self.assertEqual(self.fragment.line_number(), 13)

    def testShouldRejectNegativeOrZeroLineNumber(self):
        with self.assertRaises(ValueError):
            Fragment(self.file, 0, "blah blah")

    def testShouldExposeFile(self):
        self.assertEqual(self.fragment.file().fullname(), "main.tex")

    def testShouldRejectMissingFile(self):
        with self.assertRaises(ValueError):
            Fragment(MissingFile(ROOT / "main.tex"), 13, "blah blah")

    def testShouldExposeFragmentText(self):
        self.assertEqual(self.fragment.text(), "blah blah")

    def testShouldDetectComments(self):
        self.assertFalse(self.fragment.is_commented_out())

    def testShouldBeSliceable(self):
        self.assertEqual(self.fragment[0:4].text(), "blah")


class FlapUnitTest(FlapTest):
    """
    Provide some helper methods for create file in an in memory file system
    """

    def setUp(self):
        super().setUp()
        self.file_system = InMemoryFileSystem()
        self.listener = MagicMock(Listener())
        self.flap = Flap(self.file_system, ProcessorFactory(), self.listener)

    def run_flap(self, output=Flap.DEFAULT_OUTPUT_FILE):
        super().run_flap(output)
        self.project.create_on(self.file_system)
        self.flap.flatten(self.project.root_latex_file, self.output_directory / self.merged_file)

    def verify_listener(self, handler, fileName, lineNumber, text):
        fragment = handler.call_args[0][0]
        self.assertEqual(fragment.file().fullname(), fileName)
        self.assertEqual(fragment.line_number(), lineNumber)
        self.assertEqual(fragment.text().strip(), text)


if __name__ == "__main__":
    main()
