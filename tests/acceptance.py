
import unittest
from flatexer.FileSystem import OSFileSystem
from flatexer.path import ROOT
from flatexer.Runner import Runner

class OSFileSystemTest(unittest.TestCase):
    
    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.path = ROOT / "C:" / "temp" / "flatexer" / "test.txt"
        self.content = "blahblah blah"

        self.fileSystem.deleteDirectory(ROOT / "C:" / "temp" / "flatexer")
        self.fileSystem.deleteDirectory(ROOT / "C:" / "temp" / "flatexer_copy")
    
    def createAndOpenTestFile(self):
        self.fileSystem.createFile(self.path, self.content)
        return self.fileSystem.open(self.path)
    
    def testCreateAndOpenFile(self):
        file = self.createAndOpenTestFile()
        
        self.assertEqual(file.content(), self.content)
        
        
    def testCopyAndOpenFile(self):
        file = self.createAndOpenTestFile()
        
        copyPath = ROOT / "C:" / "temp" / "flatexer_copy"
        
        self.fileSystem.copy(file, copyPath)
        copy = self.fileSystem.open(copyPath / "test.txt")
        
        self.assertEqual(copy.content(), self.content)



class Test(unittest.TestCase):

    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.workingDir = ROOT / "C:" / "temp" / "flatexer"
        self.source = self.workingDir / "project"
        self.output = self.workingDir / "output"
        self.fileSystem.deleteDirectory(self.workingDir)
        self.fileSystem.createFile(self.source / "main.tex", "\input{result}")
        self.fileSystem.createFile(self.source / "result.tex", "\includegraphics{img/plot}")
        self.fileSystem.createFile(self.source / "img" / "plot.pdf", "\input{result}")
        self.fileSystem.createFile(self.source / "style.sty", "some style crap")
        

    def testFlattenLatexProject(self):
        Runner(self.fileSystem).run(["C:\\temp\\flatexer\\project\\main.tex", "C:\\temp\\flatexer\\output"])
        
        file = self.fileSystem.open(self.output / "merged.tex")
        self.assertEqual(file.content(), "\includegraphics{plot}")
        
        styFile = self.fileSystem.open(self.output / "style.sty")
        self.assertEqual(styFile.content(), "some style crap")


if __name__ == "__main__":
    unittest.main() 