#
# This file is part of Flap.
#
# Flap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Flap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flap.  If not, see <http://www.gnu.org/licenses/>.
#

from unittest import TestCase, main
from unittest.mock import MagicMock

from flap.FileSystem import InMemoryFileSystem, File, MissingFile
from flap.core import Flap, Fragment, Listener, CommentsRemover, Processor, IncludeSVGFixer
from flap.path import ROOT, TEMP


class FragmentTest(TestCase):
    """
    Specification of the Fragment class 
    """

    def setUp(self):
        self.file = File(None, ROOT/"main.tex", "xxx")
        self.fragment = Fragment(self.file, 13, "blah blah")
    
    def testShouldExposeLineNumber(self):
        self.assertEqual(self.fragment.lineNumber(), 13)


    def testShouldRejectNegativeOrZeroLineNumber(self):
        with self.assertRaises(ValueError):
            Fragment(self.file, 0, "blah blah")
                
    def testShouldExposeFile(self):
        self.assertEqual(self.fragment.file().fullname(), "main.tex")
        
    def testShouldRejectMissingFile(self):
        with self.assertRaises(ValueError):
            Fragment(MissingFile(ROOT/"main.tex"), 13, "blah blah")
            
    def testShouldExposeFragmentText(self):
        self.assertEqual(self.fragment.text(), "blah blah")

    def testShouldDetectComments(self):
        self.assertFalse(self.fragment.isCommentedOut())

    def testShouldBeSliceable(self):
        self.assertEqual(self.fragment[0:4].text(), "blah")



class CommentRemoverTest(TestCase):
    
    def testRemoveCommentedLines(self):
        self.runTest("\nfoo\n% this is a comment\nbar",
                     "\nfoo\n\nbar")
    
    def testRemoveEndLineComments(self):
        text = ("A"
                 "\\includegraphics[width=8cm]{%\n"
                 "foo%\n"
                 "}\n"
                 "B")
        self.runTest(text, "A\\includegraphics[width=8cm]{\nfoo\n}\nB")
    
    
    def runTest(self, text, expectation):
        source = File(None, TEMP / "test", None)
        source.isMissing = MagicMock()
        source.isMissing.return_value = False
        
        delegate = Processor()
        delegate.fragments = MagicMock()
        delegate.fragments.return_value = iter([Fragment(source, 1, text)])
        
        sut = CommentsRemover(delegate)
        
        result = list(sut.fragments())
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text(), expectation)
        


class FlapTests(TestCase):


    def setUp(self):
        self.fileSystem = InMemoryFileSystem()
        self.flap = Flap(self.fileSystem)


    def verifyFile(self, path, content):
        result = self.fileSystem.open(path)
        self.assertTrue(result.exists())
        self.assertEqual(result.content(), content)


    def testMergeInputDirectives(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", r"blahblah \input{foo} blah")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "bar")
        
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
       
        self.verifyFile(ROOT/"result"/"merged.tex", "blahblah bar blah") 
        
        
    def testMergeInputDirectiveRecursively(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "A \input{foo} Z")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "B \input{bar} Y")
        self.fileSystem.createFile(ROOT/"project"/"bar.tex", "blah")
        
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
        
        self.verifyFile(ROOT/"result"/"merged.tex", "A B blah Y Z")
  
  
    def testIncludeDirectivesAreMerged(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "blahblah \include{foo} blah")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "bar")
        
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
       
        self.verifyFile(ROOT/"result"/"merged.tex", "blahblah bar\clearpage  blah") 
        
        
    def testMissingFileAreReported(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "blahblah \input{foo} blah")
                    
        with self.assertRaises(ValueError):
            self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
            
    
    def testLinksToGraphicsAreAdjusted(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", r"A \includegraphics[width=3cm]{img/foo} Z")
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.pdf", "xyz")
         
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"merged.tex", r"A \includegraphics[width=3cm]{foo} Z")
        self.verifyFile(ROOT/"result"/"foo.pdf", "xyz")
        
        
    def testLinksToSVGAreAdjusted(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", r"A \includesvg{img/foo} Z")
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.svg", "xyz")
         
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"merged.tex", r"A \includesvg{foo} Z")
        self.verifyFile(ROOT/"result"/"foo.svg", "xyz")
    
    
    def testMultilinesDirectives(self):
        content = ("A"
                   "\includegraphics[width=8cm]{%\n"
                   "img/foo%\n"
                   "}\n"
                   "B")
        self.fileSystem.createFile(ROOT/"project"/"main.tex", content)
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.pdf", "xyz")
         
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
    
        expected = "A\\includegraphics[width=8cm]{foo}\nB"

        self.verifyFile(ROOT/"result"/"merged.tex", expected)
        self.verifyFile(ROOT/"result"/"foo.pdf", "xyz")


    def testMultilinesPath(self):
        content = ("A \\input{img/foo/%\n"
                   "bar/%\n"
                   "baz} B")
        self.fileSystem.createFile(ROOT/"project"/"main.tex", content)
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo"/"bar"/"baz.tex", "xyz")
    
        self.assertFalse(self.fileSystem.open(ROOT/"project"/"img"/"foo"/"bar"/"baz.tex").isMissing())
         
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
    
        expected = "A xyz B"

        self.verifyFile(ROOT/"result"/"merged.tex", expected)
    
    
    def testLinksToGraphicsAreRecursivelyAdjusted(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", r"AA \input{foo} AA")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", r"BB \includegraphics[width=3cm]{img/foo} BB")
        self.fileSystem.createFile(ROOT/"project"/"img"/"foo.pdf", "xyz")
        
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"merged.tex", r"AA BB \includegraphics[width=3cm]{foo} BB AA")
        self.verifyFile(ROOT/"result"/"foo.pdf", "xyz")
        
                
    def testClassFilesAreCopied(self):
        self.fileSystem.createFile(ROOT/"project"/"style.cls", "whatever")
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "xxx")
        
        self.flap.flatten(ROOT/"project"/"main.tex", ROOT/"result")
                 
        self.verifyFile(ROOT/"result"/"style.cls", "whatever")
        
    
    def testFlapNotifiesWhenMergeIsComplete(self):
        self.fileSystem.createFile(ROOT/"project"/"main.tex", "xxx")

        listener = Listener()
        listener.onFlattenComplete = MagicMock()
        flap = Flap(self.fileSystem, listener)
        
        flap.flatten(ROOT / "project" / "main.tex", ROOT / "result")

        listener.onFlattenComplete.assert_called_once_with()

        
    def testFlapNotifiesWhenAnInputDirectiveIsMet(self):
                
        self.fileSystem.createFile(ROOT/"project"/"main.tex", """blah blabh 
        \input{foo}""")
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "blah blah")

        listener = Listener()
        listener.onInput = MagicMock()
        flap = Flap(self.fileSystem, listener)
        
        flap.flatten(ROOT / "project" / "main.tex", ROOT / "result")

        fragment = listener.onInput.call_args[0][0]
        
        self.assertEqual(fragment.file().fullname(), "main.tex")
        self.assertEqual(fragment.lineNumber(), 2)
        self.assertEqual(fragment.text().strip(), "\input{foo}")
        
    
        
    def testFlapIgnoreLinesThatAreCommentedOut(self):
        content = """
            blah blah blah
            % \input{foo}
            blah blah blah
        """
        self.fileSystem.createFile(ROOT/"project"/"main.tex", content)
        self.fileSystem.createFile(ROOT/"project"/"foo.tex", "included content")

        self.flap.flatten(ROOT / "project" / "main.tex", ROOT / "result")

        merged = """
            blah blah blah
            
            blah blah blah
        """

        self.verifyFile(ROOT/"result"/"merged.tex", merged)
        
class Matcher(object):
            
    def __init__(self, model):
        self.model = model

    def __eq__(self, other):
        return (self.model.file().fullname == other.file().fullname()
            and self.model.lineNumber() == other.lineNumber()
            and self.model.text() == other.text())    

if __name__ == "__main__":
    main()