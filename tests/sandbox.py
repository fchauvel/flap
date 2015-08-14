
import unittest

from flap.ui import Controller, UI
from flap.FileSystem import OSFileSystem

class SandboxTest(unittest.TestCase):
    
    
    def testJOCC(self):
        flap = Controller(OSFileSystem(), UI())
        flap.run(["--verbose", "C:\\Users\\franckc\\home\\pub\\2015_JOCC\\main.tex",
                  "C:\\temp\\flap"])

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()