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
import itertools
from flap.path import Path


class Listener:
    """
    Handle events emitted by FLaP.
    """
    
    def on_input(self, fragment):
        """
        Triggered when an input directive was found in the LaTeX source.
        
        :param fragment: the fragment which was expanded
        :type fragment: Fragment
        """
        pass
    
    def on_include(self, fragment):
        """
        Triggered when an '\include' directive was found in the LaTeX source.
        
        :param fragment: the fragment which was expanded
        :type fragment: Fragment
        """
        pass
    
    def on_include_graphics(self, fragment):
        """
        Triggered when an 'includegraphics' directive is detected in the LaTeX source.
        
        :param fragment: the text fragment of interest
        :type fragment: Fragment
        """
        pass

    def on_include_SVG(self, fragment):
        """
        Triggered when an 'includesvg' directive is detected in the LaTeX source.
        
        :param fragment: the text fragment of interest
        :type fragment: Fragment
        """
        pass

    
    def on_flatten_complete(self):
        """
        Triggered when the flattening process is complete.
        """
        pass

    def on_missing_graphic(self, fragment):
        """
        Triggered when a graphic file referred in the given fragment could not be found

        :param fragment: the text fragment of interest
        :type fragment: Fragment
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

    def line_number(self):
        return self._lineNumber

    def file(self):
        return self._file
    
    def text(self):
        return self._text
    
    def is_commented_out(self):
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
    def input_merger(file, proxy):
        return InputFlattener(EndInputProcessor(CommentsRemover(FileWrapper(file)), proxy), proxy)

    @staticmethod
    def flap_pipeline(proxy):
        processors = [IncludeFlattener,
                      IncludeOnlyProcessor,
                      GraphicsPathProcessor,
                      IncludeGraphicsAdjuster,
                      IncludeSVGFixer,
                      OverpicAdjuster]
        pipeline = Processor.input_merger(proxy.file(), proxy)
        for eachProcessor in processors:
            pipeline = eachProcessor(pipeline, proxy)
        return pipeline


class FileWrapper(Processor):
    """
    Expose the content of a file as a (singleton) list of fragment
    """
    
    def __init__(self, file):
        self._file = file
        
    def file(self):
        return self._file
        
    def fragments(self):
        yield Fragment(self._file)


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
        for each_fragment in self._delegate.fragments():
            text = each_fragment.text()
            without_comments = re.sub(r"%(?:[^\n])*\n", "\n", text)
            each_fragment._text = without_comments
            yield each_fragment


class RegexReplacer(ProcessorDecorator):
    """
    General template method for searching and replacing a given regular expression
    in a set of fragments.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate)
        self.flap = flap

    def fragments(self):
        self.pattern = self.prepare_pattern()
        for each_fragment in self._delegate.fragments():
            for f in self.process_fragment(each_fragment): yield f

    def process_fragment(self, fragment):
        current = 0
        for eachMatch in self.all_matches(fragment):
            yield fragment[current:eachMatch.start()] 
            for f in self.replacements_for(fragment, eachMatch): yield f
            current = eachMatch.end()
        yield fragment[current:]

    def replacements_for(self, fragment, match):
        """
        :return: The list of fragments that replace the given match
        """
        pass

    def all_matches(self, fragment):
        """
        :return: All the occurrence of the pattern in the given fragment
        """
        return self.pattern.finditer(fragment.text())

    def prepare_pattern(self):
        """
        :return: The compiled pattern that is to be matched and replaced
        """
        pass

    def extract(self, container, match):
        """
        :return: a sub fragment corresponding to the given match in the container fragment
        """
        return Fragment(container.file(), container[:match.start()].text().count("\n") + 1, match.group(0))


class InputFlattener(RegexReplacer):
    """
    Detects fragments that contains an input directive (such as '\input{foo}). 
    When one is detected, it extracts all the fragments from the file that 
    is referred (such as 'foo.tex')
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)
        
    def prepare_pattern(self):
        return re.compile(r"\\input\{([^}]+)\}")
   
    def replacements_for(self, fragment, match):
        self.flap.on_input(self.extract(fragment, match))
        includedFile = self.file().sibling(match.group(1) + ".tex")
        if includedFile.isMissing():
            raise ValueError("The file '%s' could not be found." % includedFile.path())
        return Processor.input_merger(includedFile, self.flap).fragments()


class IncludeOnlyProcessor(RegexReplacer):
    """
    Detects 'includeonly' directives and notify the engine to later discard it.
    """

    def prepare_pattern(self):
        pattern = r"\\includeonly\{([^\}]+)\}"
        return re.compile(pattern)

    def replacements_for(self, fragment, match):
        included_files = re.split(",", match.group(1))
        self.flap.on_include_only(included_files)
        return []


class IncludeFlattener(InputFlattener):
    """
    Traverse the fragments available and search for next `\include{file.tex}`. It
    replaces them by the content of the file and append a \clearpage after.
    """
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return re.compile(r"\\include{([^}]+)}")

    def replacements_for(self, fragment, match):
        if self.flap.is_ignored(match.group(1)):
            return []
        else:
            return itertools.chain(super().replacements_for(fragment, match),
                                   [Fragment(fragment.file(), fragment.line_number(), "\\clearpage ")])


class GraphicsPathProcessor(RegexReplacer):
    """
    Detect the \graphicspath directive and adjust the following \includegraphics
    inclusions accordingly.
    """
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return re.compile(r"\\graphicspath{([^}]+)}")

    def replacements_for(self, fragment, match):
        """
        A \graphicspath directive is not replaced by anything.
        """
        self.flap.set_graphics_directory(match.group(1))
        return []


class IncludeGraphicsAdjuster(RegexReplacer):
    """
    Detects "\includegraphics". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """
    
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)
        
    def prepare_pattern(self):
        pattern = r"\\includegraphics\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)
    
    def replacements_for(self, fragment, match):
        path = Path.fromText(match.group(1))
        graphic = self.find_image_file(fragment, match, path)
        self.notify(self.extract(fragment, match), graphic)
        graphicInclusion = match.group(0).replace(match.group(1), graphic.basename())
        return [ Fragment(fragment.file(), fragment.line_number(), graphicInclusion) ]

    def find_image_file(self, fragment, match, path):
        directory = self.flap.get_graphics_directory()
        graphics = directory.files_that_matches(path)
        if not graphics:
            raise MissingGraphicFile(self.extract(fragment, match), match.group(1))
        graphic = None
        for each_extension in self.extensions_by_priority():
            for each_graphic in graphics:
                if each_graphic.extension() == each_extension:
                    graphic = each_graphic
        if not graphic:
            raise MissingGraphicFile(self.extract(fragment, match), match.group(1))
        return graphic
    
    def extensions_by_priority(self):
        return ["pdf", "eps", "png", "jpg"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_graphics(fragment, graphic)


class EndInputProcessor(RegexReplacer):
    """
    Discard whatever comes after an `\endinput` command.
    """

    def prepare_pattern(self):
        pattern = r"\\endinput.+\Z"
        return re.compile(pattern, re.DOTALL)

    def replacements_for(self, fragment, match):
        return []


class OverpicAdjuster(IncludeGraphicsAdjuster):
    """
    Adjust 'overpic' environment. Only the opening clause is adjusted.
    """

    def __init__(self, delegate, proxy):
        super().__init__(delegate, proxy)

    def prepare_pattern(self):
        pattern = r"\\begin{overpic}\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)


class IncludeSVGFixer(IncludeGraphicsAdjuster):
    """
    Detects "\includesvg". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """
            
    def prepare_pattern(self):
        pattern = r"\\includesvg\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)

    def extensions_by_priority(self):
        return ["svg"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_SVG(fragment, graphic)


class Flap:
    """
    The Flap engine. Does the flattening of LaTeX projects, including merging
    included files, moving graphics and resources files such as classes, styles 
    and bibliography 
    """
    
    def __init__(self, fileSystem, listener=Listener()):
        self._fileSystem = fileSystem
        self._listener = listener
        self._included_files = []
        self._graphics_directory = None
               
    def flatten(self, root, output):
        self._output = output
        try:
            self.open_file(root)
            self.merge_latex_source()
            self.copy_resource_files()
            self._listener.on_flatten_complete()
        except MissingGraphicFile as error:
            self._listener.on_missing_graphic(error.fragment())
        
    def open_file(self, source):
        self._root = self._fileSystem.open(source)
        if self._root.isMissing():
            raise ValueError("The file '%s' could not be found." % source)
        
    def file(self):
        return self._root
        
    def merge_latex_source(self):
        pipeline = Processor.flap_pipeline(self)
        fragments = pipeline.fragments()
        merge = ''.join([ f.text() for f in fragments ])
        self._fileSystem.createFile(self._output / "merged.tex", merge)
            
    def copy_resource_files(self):
        project = self._root.container()
        for eachFile in project.files():
            if self.is_resource(eachFile):
                self._fileSystem.copy(eachFile, self._output)

    def is_resource(self, eachFile):
        return eachFile.hasExtension() and eachFile.extension() in Flap.RESOURCE_FILES

    def is_ignored(self, file):
        return self._included_files and file not in self._included_files

    RESOURCE_FILES = ["cls", "sty", "bib", "bst"]       
        
    def on_input(self, fragment):
        self._listener.on_input(fragment)
    
    def on_include_graphics(self, fragment, graphicFile):
        self._fileSystem.copy(graphicFile, self._output)
        self._listener.on_include_graphics(fragment)
        
    def on_include(self, fragment):
        self._listener.on_include(fragment)
        
    def on_include_SVG(self, fragment, graphicFile):
        self._fileSystem.copy(graphicFile, self._output)
        self._listener.on_include_SVG(fragment)

    def on_include_only(self, included_files):
        self._included_files = [eachFile.strip() for eachFile in included_files]

    def set_graphics_directory(self, texPath):
        path = self.file().container().path() / texPath
        self._graphics_directory = self._fileSystem.open(path)

    def get_graphics_directory(self):
        if self._graphics_directory:
            return self._graphics_directory
        else:
            return self.file().container()


class MissingGraphicFile(Exception):
    """
    Exception thrown when a graphic file cannot be found
    """
    def __init__(self, fragment, file_name):
        super().__init__()
        self._fragment = fragment
        self._file_name = file_name

    def fragment(self):
        return self._fragment
