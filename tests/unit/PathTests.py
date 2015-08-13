
import unittest

from flap.path import Path, ROOT

class PathTests(unittest.TestCase):


    def testRoot(self):
        path = ROOT
        self.assertTrue(path.isRoot())

        
    def testPathToFile(self):
        path = (ROOT / "test" / "source.tex")
        
        self.assertFalse(path.isRoot())
        self.assertEqual(path.container(), (ROOT / "test"))
        self.assertEqual(path.fullname(), "source.tex")


    def testHasExtension(self):
        path = ROOT / "source.tex"
        
        self.assertTrue(path.hasExtension())
    
        
    def testBasename(self):
        path = ROOT / "source.tex"
        
        self.assertEqual(path.basename(), "source")
  
        
    def testContainement(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir"

        self.assertTrue(path1 in path2)

        
    def testContainmentUnderEquality(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir" / "file.txt"
        
        self.assertFalse(path1 in path2)
        self.assertFalse(path2 in path1) 


    def testPathBuilding(self):
        path = Path.fromText("\\Users\\franckc\\file.txt")
        
        self.assertEqual(path, ROOT / "Users" / "franckc" / "file.txt")


    def testParts(self):
        path = Path.fromText("C:\\Users\\franckc\\pub\\JOCC\\main.tex")
        
        self.assertEqual(path.parts(), ["C:", "Users", "franckc", "pub", "JOCC", "main.tex"])


if __name__ == "__main__":
    unittest.main()