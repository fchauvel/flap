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

from re import compile, DOTALL
from flap.engine import Fragment, Processor


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
            for f in self.process_fragment(each_fragment):
                yield f

    def process_fragment(self, fragment):
        current = 0
        for eachMatch in self.all_matches(fragment):
            self.flap.on_fragment(fragment.extract(eachMatch))
            yield fragment[current:eachMatch.start()]
            for f in self.replacements_for(fragment.extract(eachMatch), eachMatch):
                yield f
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


class LinkSubstitution(Substitution):
    """
    Detects links, such as includgraphics or bibliography. When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def replacements_for(self, fragment, match):
        reference = match.group(1)
        resource = self.find(fragment, reference)
        new_resource_name = self.flap.relocate(resource)
        replacement = fragment.replace(reference, new_resource_name)
        return [replacement]

    def find(self, fragment, reference):
        pass

    def extensions_by_priority(self):
        return ["pdf", "eps", "png", "jpg"]


class EndInput(Substitution):
    """
    Discard whatever comes after an `\endinput` command.
    """

    def prepare_pattern(self):
        return compile(r"\\endinput.+\Z", DOTALL)

    def replacements_for(self, fragment, match):
        return []


