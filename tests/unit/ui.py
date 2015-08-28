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

import re
from unittest import TestCase, main
from unittest.mock import patch

import flap
from io import StringIO
from flap.path import ROOT
from flap.core import Fragment
from flap.FileSystem import File
from flap.ui import UI 


class UiTest(TestCase):
    
    def makeUI(self, mock):
        ui = UI(mock)
        ui.enableDetails()
        return ui
    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiShowVersionNumber(self, mock):
        ui = self.makeUI(mock)        
        ui.onStartup()
        self.verifyOutputContains(mock, flap.__version__)


    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsInputDirectives(self, mock):
        ui = self.makeUI(mock)     
        self.runTest(ui.on_input, mock, ["main.tex", "3", "foo"])
    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsIncludeSVGDirectives(self, mock):
        ui = self.makeUI(mock)
        self.runTest(ui.on_include_SVG, mock, ["main.tex", "3", "foo"])

    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsInclude(self, mock):
        ui = self.makeUI(mock)        
        self.runTest(ui.on_include, mock,["main.tex", "3", "foo"])
        
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsIncludeGraphics(self, mock):
        ui = self.makeUI(mock)
        self.runTest(ui.on_include_graphics, mock, ["main.tex", "3", "foo"])

    def runTest(self, operation, mock, expectedOutputs):
        operation(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))
        for eachOutput in expectedOutputs:
            self.verifyOutputContains(mock, eachOutput)        

    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsCompletion(self, mock):
        ui = self.makeUI(mock)
        
        ui.on_flatten_complete()

        self.verifyOutputContains(mock, "complete")        

    @patch('sys.stdout', new_callable=StringIO)
    def testDisablingFragmentReport(self, mock):
        ui = self.makeUI(mock)
        ui.disableDetails()

        ui.on_include_graphics(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.assertFalse(mock.getvalue())

    def verifyOutputContains(self, mock, pattern):
        output = mock.getvalue()
        self.assertIsNotNone(re.search(pattern, output), output)
        

if __name__ == "__main__":
    main()