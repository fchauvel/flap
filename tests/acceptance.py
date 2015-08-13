
from unittest import TestCase, main

from flap.FileSystem import OSFileSystem
from flap.path import ROOT
from flap.ui import Controller

class OSFileSystemTest(TestCase):
    
    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.path = ROOT / "C:" / "temp" / "flap" / "test.txt"
        self.content = "blahblah blah"

        self.fileSystem.deleteDirectory(ROOT / "C:" / "temp" / "flap")
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



class Test(TestCase):

    def setUp(self):
        self.fileSystem = OSFileSystem()
        self.workingDir = ROOT / "C:" / "temp" / "flap"
        self.source = self.workingDir / "project"
        self.output = self.workingDir / "output"
        self.fileSystem.deleteDirectory(self.workingDir)
        self.fileSystem.createFile(self.source / "main.tex", "\input{result}")
        self.fileSystem.createFile(self.source / "result.tex", "\includegraphics{img/plot}")
        self.fileSystem.createFile(self.source / "img" / "plot.pdf", "\input{result}")
        self.fileSystem.createFile(self.source / "style.sty", "some style crap")
        

    def testFlattenLatexProject(self):
        Controller(self.fileSystem).run(["C:\\temp\\flap\\project\\main.tex", "C:\\temp\\flap\\output"])
        
        file = self.fileSystem.open(self.output / "merged.tex")
        self.assertEqual(file.content(), "\includegraphics{plot}")
        
        styFile = self.fileSystem.open(self.output / "style.sty")
        self.assertEqual(styFile.content(), "some style crap")


if __name__ == "__main__":
    main() 