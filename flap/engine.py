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
    Handle events emitted by FLaP. Errors are raised as exceptions.
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

    def extract(self, match):
        """
        :return: a sub fragment corresponding to the given match in the container fragment
        """
        line_number = self.line_number() + self[:match.start()].text().count("\n")
        text = match.group(0)
        return Fragment(self.file(), line_number, text)

    def replace(self, searched, replacement):
        changed_text = self.text().replace(searched, replacement)
        return Fragment(self._file, self.line_number(), changed_text)

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
        return Input(EndInput(CommentsRemover(FileWrapper(file)), proxy), proxy)

    @staticmethod
    def flap_pipeline(proxy):
        processors = [Include,
                      IncludeOnly,
                      GraphicsPath,
                      IncludeGraphics,
                      IncludeSVG,
                      Overpic]
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
            #without_comments = re.sub(r"[^\\]%(?:[^\n])*\n", "\n", text)
            without_comments = re.sub(r"(?<!\\|\|)%(?:[^\n]*)\n", "\n", text)
            each_fragment._text = without_comments
            yield each_fragment


class Substitution(ProcessorDecorator):
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
            for f in self.replacements_for(fragment.extract(eachMatch), eachMatch): yield f
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


class Input(Substitution):
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
        self.flap.on_input(fragment)
        included_file = self.file().sibling(match.group(1) + ".tex")
        if included_file.isMissing():
            raise TexFileNotFound(fragment)
        return Processor.input_merger(included_file, self.flap).fragments()


class IncludeOnly(Substitution):
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


class Include(Input):
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


class GraphicsPath(Substitution):
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


class IncludeGraphics(Substitution):
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
        included_graphic = match.group(1)
        graphic = self.flap.find_graphics(fragment, included_graphic, self.extensions_by_priority())
        replacement = fragment.replace(included_graphic, graphic.basename())
        self.notify(fragment, graphic)
        return [replacement]

    def extensions_by_priority(self):
        return ["pdf", "eps", "png", "jpg"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_graphics(fragment, graphic)


class EndInput(Substitution):
    """
    Discard whatever comes after an `\endinput` command.
    """

    def prepare_pattern(self):
        return re.compile(r"\\endinput.+\Z", re.DOTALL)

    def replacements_for(self, fragment, match):
        return []


class Overpic(IncludeGraphics):
    """
    Adjust 'overpic' environment. Only the opening clause is adjusted.
    """

    def __init__(self, delegate, proxy):
        super().__init__(delegate, proxy)

    def prepare_pattern(self):
        pattern = r"\\begin{overpic}\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return re.compile(pattern)


class IncludeSVG(IncludeGraphics):
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

    OUTPUT_FILE = "merged.tex"
    
    def __init__(self, fileSystem, listener=Listener()):
        self._file_system = fileSystem
        self._listener = listener
        self._included_files = []
        self._graphics_directory = None
               
    def flatten(self, root, output):
        self._output = output
        self.open_file(root)
        self.merge_latex_source()
        self.copy_resource_files()

    def open_file(self, source):
        self._root = self._file_system.open(source)
        if self._root.isMissing():
            raise ValueError("The file '%s' could not be found." % source)

    def file(self):
        return self._root
        
    def merge_latex_source(self):
        pipeline = Processor.flap_pipeline(self)
        fragments = pipeline.fragments()
        merge = ''.join([ each.text() for each in fragments ])
        self._file_system.createFile(self._output / Flap.OUTPUT_FILE, merge)
            
    def copy_resource_files(self):
        project = self._root.container()
        for eachFile in project.files():
            if self._is_resource(eachFile):
                self._file_system.copy(eachFile, self._output)

    def _is_resource(self, eachFile):
        return eachFile.hasExtension() and eachFile.extension() in Flap.RESOURCE_FILES

    def is_ignored(self, file):
        return self._included_files and file not in self._included_files

    def find_graphics(self, fragment, text_path, extensions_by_priority):
        candidates = self.graphics_directory().files_that_matches(Path.fromText(text_path))
        for each_extension in extensions_by_priority:
            for each_graphic in candidates:
                if each_graphic.extension() == each_extension:
                    return each_graphic
        raise GraphicNotFound(fragment)

    RESOURCE_FILES = ["cls", "sty", "bib", "bst"]       
        
    def on_input(self, fragment):
        self._listener.on_input(fragment)
    
    def on_include_graphics(self, fragment, graphicFile):
        self._file_system.copy(graphicFile, self._output)
        self._listener.on_include_graphics(fragment)
        
    def on_include(self, fragment):
        self._listener.on_include(fragment)
        
    def on_include_SVG(self, fragment, graphicFile):
        self._file_system.copy(graphicFile, self._output)
        self._listener.on_include_SVG(fragment)

    def on_include_only(self, included_files):
        self._included_files = [each_file.strip() for each_file in included_files]

    def set_graphics_directory(self, texPath):
        path = self.file().container().path() / texPath
        self._graphics_directory = self._file_system.open(path)

    def graphics_directory(self):
        if self._graphics_directory:
            return self._graphics_directory
        else:
            return self.file().container()


class ResourceNotFound(Exception):

    def __init__(self, fragment):
        self._fragment = fragment

    def fragment(self):
        return self._fragment


class GraphicNotFound(ResourceNotFound):
    """
    Exception thrown when a graphic file cannot be found
    """
    def __init__(self, fragment):
        super().__init__(fragment)


class TexFileNotFound(ResourceNotFound):
    """
    Exception thrown when a LaTeX source file cannot be found
    """

    def __init__(self, fragment):
        super().__init__(fragment)
