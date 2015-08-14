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
    
    def onIncludeGraphics(self, fragment):
        """
        Triggered when an 'includegraphics' directive is detected in the LaTeX source.
        
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
    
    def __init__(self, file, lineNumber, text):
        if lineNumber < 1:
            raise ValueError("Line number must be strictly positive (found %d)" % lineNumber)
        self._lineNumber = lineNumber
        if file.isMissing():
            raise ValueError("Missing file '%s'" % file.fullname())
        self._file = file
        self._text = text

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
        return InputFlattener(CommentRemover(LineExtractor(file)), proxy)

    @staticmethod
    def flapPipeline(proxy):
        return IncludeGraphicsAdjuster(Processor.inputMerger(proxy.file(), proxy), proxy)


class LineExtractor(Processor):
    """
    Expose all the line of a file as fragments
    """
    
    def __init__(self, file):
        super().__init__()
        self._file = file

    def file(self):
        return self._file
    
    def fragments(self):
        for (line, text) in enumerate(self.lines()):
            yield Fragment(self._file, line+1, text)

    def lines(self):
        yield from self._file.content().splitlines(True)


class ProcessorDecorator(Processor):
    """
    Abstract Decorator for processors
    """

    def __init__(self, delegate):
        super().__init__()
        self._delegate = delegate

    def file(self):
        return self._delegate.file()

    
class CommentRemover(ProcessorDecorator):
    """
    Processor decorator (cf. GoF), which breaks down the file content into lines
    and remove the one that are commented
    """
    
    def __init__(self, delegate):
        super().__init__(delegate)    
            
    def fragments(self):
        for eachFragment in self._delegate.fragments():
            if not eachFragment.isCommentedOut():
                yield eachFragment                
        
        
class InputFlattener(ProcessorDecorator):
    """
    Goes through the fragments available, and detects those that contains an
    input directive (such as '\input{foo}). When on is detected, it extracts all
    the fragments from the file that is referred (such as 'foo.tex')
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate)
        self.flap = flap
    
    def fragments(self):
        for eachFragment in self._delegate.fragments():
            yield from self.flattenInput(eachFragment)
        
    def flattenInput(self, fragment):
        current = 0
        for eachInput in self.allInputDirectives(fragment):
            self.flap.onInput(fragment)
            yield fragment[current:eachInput.start() - 1]
            yield from self.fragmentsFrom(eachInput.group(1))
            current = eachInput.end()
        yield fragment[current:]

    def allInputDirectives(self, fragment):
        return InputFlattener.PATTERN.finditer(fragment.text())


    PATTERN = re.compile("\\input{([^}]+)}")

   
    def fragmentsFrom(self, fileName):
        includedFile = self.file().sibling(fileName + ".tex")
        if includedFile.isMissing():
            raise ValueError("The file '%s' could not be found." % includedFile.path())
        return Processor.inputMerger(includedFile, self.flap).fragments()



class IncludeGraphicsAdjuster(ProcessorDecorator):
    """
    Check whether fragments contains a graphic inclusion directive (such as 
    \includegraphics{img/foo}). When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate)
        self.flap = flap

    def fragments(self):
        for eachFragment in self._delegate.fragments():
            current = 0
            for match in self.allIncludeGraphics(eachFragment):
                yield eachFragment[current: match.start()-1]    
                yield self.adjustIncludeGraphics(eachFragment, match)
                current = match.end()
            yield eachFragment[current:]

    def allIncludeGraphics(self, eachFragment):
        return IncludeGraphicsAdjuster.PATTERN.finditer(eachFragment.text())

    def adjustIncludeGraphics(self, fragment, match):
        path = Path.fromText(match.group(1))
        graphics = fragment.file().container().filesThatMatches(path)
        if not graphics:
            raise ValueError("Unable to find file for graphic '%s' in '%s'" % (match.group(1), fragment.file().container().path()))
        else:
            graphic = graphics[0]
            self.flap.onIncludeGraphics(fragment, graphic)
            graphicInclusion = match.group(0).replace(match.group(1), graphic.basename())
            return Fragment(fragment.file(), fragment.lineNumber(), "\\" + graphicInclusion)



    PATTERN = re.compile("\\includegraphics(?:\[[^\]]+\])*\{([^\}]+)\}")


 

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
            if eachFile.hasExtension() and eachFile.extension() in Flap.RESOURCE_FILES:
                self._fileSystem.copy(eachFile, self._output)

    RESOURCE_FILES = ["cls", "sty", "bib", "bst"]       
        
    def onInput(self, fragment):
        self._listener.onInput(fragment)
    
    def onIncludeGraphics(self, fragment, graphicFile):
        self._fileSystem.copy(graphicFile, self._output)
        self._listener.onIncludeGraphics(fragment)   
           
    