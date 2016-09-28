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

from flap.engine import Fragment
from flap.substitutions.commons import Substitution


class FileSubstitution(Substitution):
    """
    Replace the link to a TeX file by its content
    """

    def replacements_for(self, fragment, match):
        included_file = self.flap.find_tex_source(fragment, match.group(1), self.tex_file_extensions())
        return self.flap.raw_fragments_from(included_file)

    @staticmethod
    def tex_file_extensions():
        return ["tex"]


class Input(FileSubstitution):
    """
    Detects fragments that contains an input directive (such as '\input{foo}).
    When one is detected, it extracts all the fragments from the file that
    is referred (such as 'foo.tex')
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\input\s*\{([^}]+)\}")


class SubFile(FileSubstitution):
    """
    Detects fragments that contains an subfile directive (i.e., '\subfile{foo}').
    When one is detected, it extracts all the fragments from the file that
    is referred (such as 'foo.tex')
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\subfile\{([^}]+)\}")


class SubFileExtractor(Substitution):
    """
    Extract the content of the 'subfile', that is the text between
    \begin{document} and \end{document}.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\documentclass(?:\[[^\]]+\])?\{subfiles\}.*\\begin\{document\}(.+)\\end\{document\}", DOTALL)

    def replacements_for(self, fragment, match):
        if match is None:
            raise ValueError("This is not a valid subfile!")
        return [fragment.extract(match, 1)]


class IncludeOnly(Substitution):
    """
    Detects '\includeonly' directives and notify the engine to later
    discard the specified files.
    """

    def prepare_pattern(self):
        return compile(r"\\includeonly\{([^\}]+)\}")

    def replacements_for(self, fragment, match):
        included_files = split(",", match.group(1))
        self.flap.restrict_inclusion_to(included_files)
        return []


class Include(Input):
    """
    Matches `\include{file.tex}`. It replaces them by the content of the
    file and append a \clearpage after.
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
