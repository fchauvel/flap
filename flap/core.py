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

import re
from flap.path import Path


class Listener:
    """
    Handle events emitted by FLaP.
    """
    
    def onInput(self, fragment):
        """
        Triggered when an input directive was found in the LaTeX source.
        
        :param fragment: the fragment which was expanded
        :type fragment: Fragment
        """
        pass
    
    def onInclude(self, fragment):
        """
        Triggered when an '\include' directive was found in the LaTeX source.
        
        :param fragment: the fragment which was expanded
        :type fragment: Fragment
        """
        pass
    
    def onIncludeGraphics(self, fragment):
        """
        Triggered when an 'includegraphics' directive is detected in the LaTeX source.
        
        :param fragment: the text fragment of interest
        :type fragment: Fragment
        """
        pass

    def onIncludeSVG(self, fragment):
        """
        Triggered when an 'includesvg' directive is detected in the LaTeX source.
        
        :param fragment: the text fragment of interest
        :type fragment: Fragment
        """
        pass

    
    def onFlattenComplete(self):
        """
        Triggered when the flattening process is complete.
        """
        pass
    


class Fragment:
    """
    A fragment of text, taken from a line in a file
    """
    
    def __init__(self, file, lineNumber=1, text=None):
        if lineNumber < 1:
            raise ValueError("Line number must be strictly positive (found %d)" % lineNumber)
        self._lineNumber = lineNumber
        if file.isMissing():
            raise ValueError("Missing file '%s'" % file.fullname())
        self._file = file
        self._text = text if text is not None else self._file.content()
        

    def lineNumber(self):
        return self._lineNumber

    def file(self):
        return self._file
    
    def text(self):
        return self._text
    
    def isCommentedOut(self):
        return self._text.strip().startswith("%")

    def __getitem__(self, key):
        return Fragment(self._file, self._lineNumber, self._text[key])
    

class Processor:
    """
    Interface of a processor, exposes a list of fragments.
    """
    
    def file(self):
        pass
    
    def fragments(self):
        pass

    @staticmethod
    def inputMerger(file, proxy):
        return InputFlattener(CommentsRemover(FileWrapper(file)), proxy)

    @staticmethod
    def flapPipeline(proxy):
        return IncludeSVGFixer(IncludeGraphicsAdjuster(IncludeFlattener(Processor.inputMerger(proxy.file(), proxy), proxy), proxy), proxy)


class FileWrapper(Processor):
    """
    Expose the content of a file as a (singleton) list of fragment
    """
    
    def __init__(self, file):
        self._file = file
        
    def file(self):
        return self._file
        
    def fragments(self):
        yield from [ Fragment(self._file) ]


class ProcessorDecorator(Processor):
    """
    Abstract Decorator for processors
    """

    def __init__(self, delegate):
        super().__init__()
        self._delegate = delegate

    def file(self):
        return self._delegate.file()


class CommentsRemover(ProcessorDecorator):
    
    def __init__(self, delegate):
        super().__init__(delegate)
    
    def fragments(self):
        for eachFragment in self._delegate.fragments():
            text = eachFragment.text()
            withoutComments = re.sub(r"%(?:[^\n])*\n", "\n", text)
            eachFragment._text = withoutComments
            yield eachFragment


class RegexReplacer(ProcessorDecorator):
    """
    General template method for searching and replacing a given regular expression
    in a set of fragments.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate)
        self.flap = flap

    def fragments(self):
        self.pattern = self.preparePattern()
        for eachFragment in self._delegate.fragments():
            yield from self.processFragment(eachFragment)

    def processFragment(self, fragment):
        current = 0
        for eachMatch in self.allMatches(fragment):
            yield fragment[current:eachMatch.start()] 
            yield from self.replacementsFor(fragment, eachMatch)
            yield self.suffixFragment(fragment, eachMatch)
            current = eachMatch.end()
        yield fragment[current:]

    def replacementsFor(self, fragment, match):
        """
        :return: The list of fragments that replace the given match
        """
        pass

    def suffixFragment(self, fragment, match):
        """
        :return: An additional fragment that shall be appended just after the replacement
        """
        return Fragment(fragment.file(), fragment.lineNumber(), "")

    def allMatches(self, fragment):
        """
        :return: All the occurrence of the pattern in the given fragment
        """
        return self.pattern.finditer(fragment.text())

    def preparePattern(self):
        """
        :return: The compiled pattern that is to be matched and replaced
        """
        pass
    
class IncludeFlattener(RegexReplacer):
    """
    Traverse the fragments available and search for nest `\include{file.tex}`. It
    replaces them by the content of the file and append a \clearpage after.
    """
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def preparePattern(self):
        return re.compile(r"\\include{([^}]+)}")
   
    def replacementsFor(self, fragment, match):
        self.flap.onInclude(Fragment(fragment.file(), fragment[:match.start()].text().count("\n") + 1, match.group(0)))
        includedFile = self.file().sibling(match.group(1) + ".tex")
        if includedFile.isMissing():
            raise ValueError("The file '%s' could not be found." % includedFile.path())
        return Processor.inputMerger(includedFile, self.flap).fragments() 
    
    def suffixFragment(self, fragment, match):
        return Fragment(fragment.file(), fragment.lineNumber(), "\\clearpage ")
      
        
class InputFlattener(RegexReplacer):
    """
    Detects fragments that contains an input directive (such as '\input{foo}). 
    When one is detected, it extracts all the fragments from the file that 
    is referred (such as 'foo.tex')
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)
        
    def preparePattern(self):
        return re.compile(r"\\input\{([^}]+)\}")
            
    def replacementsFor(self, fragment, match):
        self.flap.onInput(Fragment(fragment.file(), fragment[:match.start()].text().count("\n") + 1, match.group(0)))
        includedFile = self.file().sibling(match.group(1) + ".tex")
        if includedFile.isMissing():
            raise ValueError("The file '%s' could not be found." % includedFile.path())
        return Processor.inputMerger(includedFile, self.flap).fragments()



class IncludeGraphicsAdjuster(RegexReplacer):
    """
    Detects "\includegraphics". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)
        
    def preparePattern(self):
        pattern = r"\\includegraphics\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)
    
    def replacementsFor(self, fragment, match):
        path = Path.fromText(match.group(1).strip())
        graphics = fragment.file().container().filesThatMatches(path)
        if not graphics:
            raise ValueError("Unable to find file for graphic '%s' in '%s'" % (match.group(1), fragment.file().container().path()))
        else:
            graphic = graphics[0]
            self.notify(fragment, graphic)
            graphicInclusion = match.group(0).replace(match.group(1), graphic.basename())
            return [ Fragment(fragment.file(), fragment.lineNumber(), graphicInclusion) ]

    def notify(self, fragment, graphic):
        return self.flap.onIncludeGraphics(fragment, graphic)

class IncludeSVGFixer(IncludeGraphicsAdjuster):
    """
    Detects "\includesvg". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """
            
    def preparePattern(self):
        pattern = r"\\includesvg\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)

    def notify(self, fragment, graphic):
        return self.flap.onIncludeSVG(fragment, graphic)

class Flap:
    """
    The Flap engine. Does the flattening of LaTeX projects, including merging
    included files, moving graphics and resources files such as classes, styles 
    and bibliography 
    """
    
    def __init__(self, fileSystem, listener=Listener()):
        self._fileSystem = fileSystem
        self._listener = listener
               
    def flatten(self, root, output):
        self._output = output
        self.openFile(root)
        self.mergeLaTeXSource()
        self.copyResourceFiles()
        self._listener.onFlattenComplete()
        
    def openFile(self, source):
        self._root = self._fileSystem.open(source)
        if self._root.isMissing():
            raise ValueError("The file '%s' could not be found." % source)
        
    def file(self):
        return self._root
        
    def mergeLaTeXSource(self):
        pipeline = Processor.flapPipeline(self)
        fragments = pipeline.fragments()
        merge = ''.join([ f.text() for f in fragments ])
        self._fileSystem.createFile(self._output / "merged.tex", merge)
            
    def copyResourceFiles(self):
        project = self._root.container()
        for eachFile in project.files():
            if self.isResource(eachFile):
                self._fileSystem.copy(eachFile, self._output)

    def isResource(self, eachFile):
        return eachFile.hasExtension() and eachFile.extension() in Flap.RESOURCE_FILES


    RESOURCE_FILES = ["cls", "sty", "bib", "bst"]       
        
    def onInput(self, fragment):
        self._listener.onInput(fragment)
    
    def onIncludeGraphics(self, fragment, graphicFile):
        self._fileSystem.copy(graphicFile, self._output)
        self._listener.onIncludeGraphics(fragment)   
        
    def onInclude(self, fragment):
        self._listener.onInclude(fragment)
        
    def onIncludeSVG(self, fragment, graphicFile):
        self._fileSystem.copy(graphicFile, self._output)
        self._listener.onIncludeSVG(fragment)   
    