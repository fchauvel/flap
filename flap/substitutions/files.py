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

from re import compile, split, DOTALL
from itertools import chain

from flap.engine import Fragment, TexFileNotFound
from flap.substitutions.commons import Substitution


class Input(Substitution):
    """
    Detects fragments that contains an input directive (such as '\input{foo}).
    When one is detected, it extracts all the fragments from the file that
    is referred (such as 'foo.tex')
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\input\{([^}]+)\}")

    def replacements_for(self, fragment, match):
        self.flap.on_input(fragment)
        file_name = match.group(1) if match.group(1).endswith(".tex") else match.group(1) + ".tex"
        included_file = self.flap.locate(file_name)
        if included_file.isMissing():
            raise TexFileNotFound(fragment)
        return self.flap._processors.input_merger(included_file, self.flap).fragments()


class SubFile(Substitution):
    """
    Detects fragments that contains an subfile directive (i.e., '\subfile{foo}).
    When one is detected, it extracts all the fragments from the file that
    is referred (such as 'foo.tex')
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\subfile\{([^}]+)\}")

    def replacements_for(self, fragment, match):
        self.flap.on_input(fragment) # TODO: Update this line
        included_file = self.file().sibling(match.group(1) + ".tex")
        if included_file.isMissing():
            raise TexFileNotFound(fragment)
        return self.flap._processors.input_merger(included_file, self.flap).fragments()


class SubFileExtractor(Substitution):
    """
    Extract the content of the 'subfile', that is the text between \begin{document} and \end{document}.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\documentclass.*\{subfiles\}.*\\begin\{document\}(.+)\\end\{document\}", DOTALL)

    def replacements_for(self, fragment, match):
        if match is None:
            raise ValueError("This is not a valid subfile!")
        return [fragment.extract(match, 1)]


class IncludeOnly(Substitution):
    """
    Detects 'includeonly' directives and notify the engine to later discard it.
    """

    def prepare_pattern(self):
        pattern = r"\\includeonly\{([^\}]+)\}"
        return compile(pattern)

    def replacements_for(self, fragment, match):
        included_files = split(",", match.group(1))
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
        return compile(r"\\include{([^}]+)}")

    def replacements_for(self, fragment, match):
        if self.flap.is_ignored(match.group(1)):
            return []
        else:
            return chain(super().replacements_for(fragment, match),
                                   [Fragment(fragment.file(), fragment.line_number(), "\\clearpage ")])
