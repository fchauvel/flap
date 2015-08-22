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

from unittest import TestCase, main, skip

from flap.ui import Controller, UI
from flap.FileSystem import OSFileSystem

  
class RegexText(TestCase):
    
    def testMultilineMatch(self):
        text = """
        \\includegraphics[width=3cm]{%
            img/foo/text}
        """
        pattern = re.compile(r"\includegraphics\s*(?:\[([^\]]+)\])\{([^\}]+)\}")
        
        match = re.search(pattern, text)      
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "width=3cm")
        self.assertEqual(self.discardComments(match.group(2)), "img/foo/text")
        
        lineNumber = text[:match.start()].count("\n")
        self.assertEqual(lineNumber, 1)


    def discardComments(self, text):
        return re.sub(r"%[^\\n]", "", text).strip()
        
@skip("Sandbox")
class SandboxTest(TestCase):
    
    
    def testJOCC(self):
        flap = Controller(OSFileSystem(), UI())
        flap.run(["--verbose", "C:\\Users\\franckc\\home\\pub\\2015_JOCC\\main.tex",
                  "C:\\temp\\flap"])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    main()