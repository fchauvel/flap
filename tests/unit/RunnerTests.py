
import unittest
import tempfile


from flatexer.Runner import Command 


class Test(unittest.TestCase):


    def testCommandShallHaveADefaultOutputDirectory(self):
        command = Command()
        
        self.assertEqual(command.outputDirectory(), tempfile.gettempdir())


    def testCommandShallHaveADefaultRootTeXFile(self):
        command = Command()
        
        self.assertEqual(command.rootFile(), "main.tex")
       
        
    def testParsingCommandLine(self):
        command = Command.parse(["main.tex", "result"])
        
        self.assertEqual(command.rootFile(), "main.tex")
        self.assertEqual(command.outputDirectory(), "result") 


if __name__ == "__main__":
    unittest.main()