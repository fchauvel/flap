from unittest import TestCase, main
from unittest.mock import MagicMock

from flap.lexer import Lexer, Source
from flap.parser import Automaton


class AutomatonTest(TestCase):
    
    def setUp(self):
        self.automaton = Automaton()
    
    def testDetectCommand(self):
        self.feed("\\text ")
        self.assertEquals(len(self.matches()), 1)    
    
    def runTest(self, text, expectedCount):
        self.feed(text)
        self.assertEquals(len(self.matches()), expectedCount)
        
    def feed(self, text):
        source = Source()
        source.text = MagicMock()
        source.text.return_value = text
        fragments = Lexer(source).breakUp()
        self.automaton.acceptAll(fragments)

    def matches(self):
        return self.automaton.matches()

    def testWithoutTrailingSpace(self):
        self.runTest("\\text", 1)       
       
    def testWithManyInSequence(self):
        self.runTest("\\text \\text ", 2)
                
    def testWithCommentAfterOpeningOption(self):
        self.runTest("\\text[%\nfoo]{foo}  ", 1)

    def testWithCommentBetweenOptionAndArgument(self):
        self.runTest("\\text[foo]%\n{foo}  ", 1)
        
    def testWithCommentAfterOpeningArgument(self):
        self.runTest("\\text[foo]{%\nfoo}  ", 1)
    
    def testWithSimpleDocument(self):
        text = r"""
        \documentclass{article}
        
        \begin{document}
            Here is a nice document
            \includegraphics[width=3cm]{%
                img/text/file/test}
            That was a cool document
        \end{document}
        """
        self.runTest(text, 4)



class CaptureTest(TestCase):
    
    def testSimpleCommand(self):
        self.runTest("\\text", 
                     name="\\text", 
                     options=[], 
                     parameters=[])  
        
    def testCommandWithOneOption(self):
        self.runTest("\\text[foo]", 
                     name="\\text", 
                     options=["foo"], 
                     parameters=[])  
        
    def testCommandWithOneParameter(self):
        self.runTest("\\text{foo}", 
                     name="\\text", 
                     options=[], 
                     parameters=["foo"])  

    def testCommandWithOneOptionAndOneParameter(self):
        self.runTest("\\text[blahblah]{foo}", 
                     name="\\text", 
                     options=["blahblah"], 
                     parameters=["foo"])  


    def runTest(self, text, name, options, parameters):
        matches = self.parse(text)
        self.assertEqual(len(matches), 1, "Wrong number of match")
        self.assertEqual(matches[0].name(), name, "wrong command")
        self.assertEqual(matches[0].options(), options, "wrong options")
        self.assertEqual(matches[0].parameters(), parameters, "wrong parameters") 

    def parse(self, text):
        automaton = Automaton()
        source = Source()
        source.text = MagicMock()
        source.text.return_value = text
        fragments = Lexer(source).breakUp()
        automaton.acceptAll(fragments)
        matches = automaton.matches()
        return matches

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    main()