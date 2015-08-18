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
        
        ui.onInput(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.verifyOutputContains(mock, "main.tex")        
        self.verifyOutputContains(mock, "3")        
        self.verifyOutputContains(mock, "foo")        
        
        
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsInclude(self, mock):
        ui = self.makeUI(mock)
        
        ui.onInclude(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.verifyOutputContains(mock, "main.tex")        
        self.verifyOutputContains(mock, "3")        
        self.verifyOutputContains(mock, "foo")        
        
        
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsIncludeGraphics(self, mock):
        ui = self.makeUI(mock)
        
        ui.onIncludeGraphics(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.verifyOutputContains(mock, "main.tex")        
        self.verifyOutputContains(mock, "3")        
        self.verifyOutputContains(mock, "foo")        

    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsCompletion(self, mock):
        ui = self.makeUI(mock)
        
        ui.onFlattenComplete()

        self.verifyOutputContains(mock, "complete")        

    @patch('sys.stdout', new_callable=StringIO)
    def testDisablingFragmentReport(self, mock):
        ui = self.makeUI(mock)
        ui.disableDetails()

        ui.onIncludeGraphics(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.assertFalse(mock.getvalue())

    def verifyOutputContains(self, mock, pattern):
        output = mock.getvalue()
        self.assertIsNotNone(re.search(pattern, output), output)
        

if __name__ == "__main__":
    main()