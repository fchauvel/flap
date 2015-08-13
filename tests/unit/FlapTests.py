
from unittest import TestCase, main
from unittest.mock import MagicMock

from flap.FileSystem import InMemoryFileSystem
from flap.core import Flap, Listener 
from flap.path import ROOT


class FlapTests(TestCase):


    def setUp(self):
        self.fileSystem = InMemoryFileSystem()
        self.flatexer = Flap(self.fileSystem)


    def verifyFile(self, path, content):
        result = self.fileSystem.open(path)
        self.assertTrue(result.exists())
        self.assertEqual(result.content(), content)


    def testMergeInputDirectives(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "blahblah \input{foo} blah")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "bar")
        
        self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
       
        self.verifyFile(ROOT/"result"/"merged.tex", "blahblah bar blah") 
        
        
    def testMergeInputDirectiveRecursively(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "A \input{foo} Z")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "B \input{bar} Y")
        self.fileSystem.createFile(ROOT/"project"/"bar.tex", "blah")
        
        self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
        
        self.verifyFile(ROOT/"result"/"merged.tex", "A B blah Y Z")
  
        
    def testMissingFileAreReported(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "blahblah \input{foo} blah")
                    
        with self.assertRaises(ValueError):
            self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
            
            
    def testLinksToGraphicsAreAdjusted(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "A \includegraphics[width=3cm]{img/foo} Z")
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.pdf", "xyz")
         
        self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"merged.tex", "A \includegraphics[width=3cm]{foo} Z")
        self.verifyFile(ROOT/"result"/"foo.pdf", "xyz")
    
    
    def testLinksToGraphicsAreRecursivelyAdjusted(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "AA \input{foo} AA")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "BB \includegraphics[width=3cm]{img/foo} BB")
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.pdf", "xyz")
        
        self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"merged.tex", "AA BB \includegraphics[width=3cm]{foo} BB AA")
        self.verifyFile(ROOT/"result"/"foo.pdf", "xyz")
        
        
    def testClassFilesAreCopied(self):
        self.fileSystem.createFile(ROOT/"project"/"style.cls", "whatever")
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "xxx")
        
        self.flatexer.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"style.cls", "whatever")
        
    
    def testFlapNotifiesWhenMergeIsComplete(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "xxx")

        listener = Listener()
        listener.onFlattenComplete = MagicMock()
        flap = Flap(self.fileSystem, listener)
        
        flap.flatten(ROOT / "project" / "main.tex", ROOT / "result")

        listener.onFlattenComplete.assert_called_once_with()
        
        
if __name__ == "__main__":
    main()