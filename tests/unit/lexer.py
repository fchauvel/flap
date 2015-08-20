
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
            
         
    def testBreakDownIncludeCommands(self):
        lexer = self.makeLexer(r"\include{foo}")
        
        fragments = [ fragment.text() for fragment in lexer.breakUp() ]
        
        self.assertEqual(fragments, [r"\include", r"{", r"foo", r"}"])

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

    def makeLexer(self, text):
        source = Source()
        source.text = MagicMock()
        source.text.return_value = text
        return Lexer(source)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    main()