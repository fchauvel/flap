
import unittest


class SandboxTest(unittest.TestCase):
    
    
    def testFoo(self):
        self.assertTrue(True)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()