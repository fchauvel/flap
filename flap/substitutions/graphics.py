
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

from re import compile
from flap.substitutions.commons import Substitution, LinkSubstitution


class GraphicsPath(Substitution):
    """
    Detect the \graphicspath directive and adjust the following \includegraphics
    inclusions accordingly.
    """
    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return compile(r"\\graphicspath{{?([^}]+)}?}")

    def replacements_for(self, fragment, match):
        """
        A \graphicspath directive is not replaced by anything.
        """
        self.flap.set_graphics_directory(match.group(1))
        return []


class IncludeGraphics(LinkSubstitution):
    """
    Detects "\includegraphics". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        pattern = r"\\includegraphics\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return compile(pattern)

    def find(self, fragment, reference):
        return self.flap.find_graphics(fragment, reference, self.extensions_by_priority())

    def extensions_by_priority(self):
        return ["pdf", "eps", "png", "jpg"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_graphics(fragment, graphic)


class Overpic(IncludeGraphics):
    """
    Adjust 'overpic' environment. Only the opening clause is adjusted.
    """

    def __init__(self, delegate, proxy):
        super().__init__(delegate, proxy)

    def prepare_pattern(self):
        pattern = r"\\begin{overpic}\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return compile(pattern)


class IncludeSVG(IncludeGraphics):
    """
    Detects "\includesvg". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """

    def prepare_pattern(self):
        pattern = r"\\includesvg\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}"
        return compile(pattern)

    def extensions_by_priority(self):
        return ["svg"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_SVG(fragment, graphic)
