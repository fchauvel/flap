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
import os
import subprocess

from unittest import TestCase, main, skip

from flap.ui import Controller, UI
from flap.FileSystem import OSFileSystem

  
@skip("Sandbox")
class SandboxTest(TestCase):        

    def testCallingGit(self):
        environment = os.environ.copy()
        environment["PATH"] += """;C:/Program Files (x86)/Git/bin/"""
        print(environment["PATH"])
        subprocess.call(["git.exe", "log"], env=environment, shell=True)
    
    
    def testJOCC(self):
        flap = Controller(OSFileSystem(), UI())
        flap.run(["--verbose", "C:\\Users\\franckc\\home\\pub\\2015_JOCC\\main.tex",
                  "C:\\temp\\flap"])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    main()