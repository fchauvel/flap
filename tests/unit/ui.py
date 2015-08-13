
import re
from unittest import TestCase, main
from unittest.mock import patch

from io import StringIO
import tempfile


from flap.ui import Command, UI 


class UiTest(TestCase):
    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiShowVersionNumber(self, mock):
        ui = UI(mock)
        
        ui.onStartup()
        
        self.verifyOutputContains(mock, "v0.1")


    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsInputDirectives(self, mock):
        ui = UI(mock)
        
        ui.onInput("foo")

        self.verifyOutputContains(mock, " - input: foo")        

    
    @patch('sys.stdout', new_callable=StringIO)
    def testUiReportsCompletion(self, mock):
        ui = UI(mock)
        
        ui.onFlattenComplete()

        self.verifyOutputContains(mock, "complete")        


    def verifyOutputContains(self, mock, pattern):
        output = mock.getvalue()
        self.assertIsNotNone(re.search(pattern, output), output)
        


class Test(TestCase):


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
    main()