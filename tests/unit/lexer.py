
from flap.lexer import Lexer, Source, Position

from unittest import TestCase, main 
from unittest.mock import MagicMock

class LexerTest(TestCase):

    def testFullLaTeXDocument(self):
        source = r"""
% This is a sample document
\documentclass[11pt]{article}

\begin{document}
    Bonjour \& les enfants
    \input{foo.tex}
\end{document}
        """   
        lexer = self.makeLexer(source)
        print("\n".join([ str(fragment) for fragment in lexer.breakUp()]))
            
    def testBreakDownCommands(self):
        self.checkFragmentText("\\include", ["\\include"])
    
    def checkFragmentText(self, text, expected):
        lexer = self.makeLexer(text)        
        fragments = [ fragment.text() for fragment in lexer.breakUp() ]
        self.assertEquals(fragments, expected)
         
    def makeLexer(self, text):
        source = Source()
        source.text = MagicMock()
        source.text.return_value = text
        return Lexer(source)
        
    def testBreakDownCommandsWithOneOption(self):
        self.checkFragmentText("\\include[foo]", ["\\include", "[", "foo", "]"])
        self.checkFragmentText("\\text[foo]", ["\\text", "[", "foo", "]"])
        
    def testBreakDownCommandsWithManyOptions(self):
        self.checkFragmentText("\\include[foo][bar]", ["\\include", "[", "foo", "]", "[", "bar", "]"])
        
    def testBreakDownCommandsWithOneParameter(self):
        self.checkFragmentText("\\include{foo}", ["\\include", "{", "foo", "}"])
        
    def testBreakDownCommandsWithManyParameter(self):
        self.checkFragmentText("\\include{foo}{bar}", ["\\include", "{", "foo", "}", "{", "bar", "}"])
        
    def testBreakDownCommandWithOneOptionAndOneParameter(self):
        self.checkFragmentText("\\include[bla]{foo}", ["\\include", "[", "bla", "]", "{", "foo", "}"])
        
        
    def testDetectCommentsAfterASymbol(self):
        lexer = self.makeLexer("\\include{% this is a comment\nfoo}")

        fragments = list(lexer.breakUp())
        
        self.assertEqual(fragments[2].type(), "comment", fragments)
        self.assertEqual(fragments[2].text(), r"% this is a comment", fragments)
        
    def testDetectCommentsBeforeASymbol(self):
        lexer = self.makeLexer("\\include% this is a comment\n{foo}")

        fragments = list(lexer.breakUp())
        
        self.assertEqual(fragments[1].type(), "comment", fragments)
        self.assertEqual(fragments[1].text(), r"% this is a comment", fragments)

    def testFragmentType(self):
        lexer = self.makeLexer(r"\include{foo}")
        
        fragments = list(lexer.breakUp())
        self.assertEqual(fragments[0].type(), "command", fragments)
        
    def testCountLines(self):
        lexer = self.makeLexer("line1\nline2\nline3\n")
        
        fragments = list(lexer.breakUp())
        
        self.assertEqual(fragments[0].position(), Position(1,1), fragments)
        self.assertEqual(fragments[2].position(), Position(2,1), fragments)
        self.assertEqual(fragments[4].position(), Position(3,1), fragments)

   



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    main()