#!/usr/bin/env python

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


from flap.latex.macros.core import Begin, Def, DocumentClass, \
    Macro, RequirePackage, UsePackage
from flap.latex.macros.graphics import IncludeGraphics, IncludeSVG, \
    GraphicsPath, Overpic
from flap.latex.macros.bibliography import Bibliography, \
    BibliographyStyle, MakeIndex
from flap.latex.macros.inlining import EndInput, Include, IncludeOnly, \
    Input, SubFile
from flap.latex.macros.listings import Verbatim
from flap.latex.macros.biblatex import AddBibResource


class MacroFactory:
    """
    Create macros that are associated with a given FLaP backend
    """

    def __init__(self, flap):
        self._flap = flap
        self._macros = [
            Begin(self._flap),
            Bibliography(self._flap),
            BibliographyStyle(self._flap),
            AddBibResource(self._flap),
            Def(self._flap),
            DocumentClass(self._flap),
            EndInput(self._flap),
            GraphicsPath(self._flap),
            IncludeGraphics(self._flap),
            IncludeOnly(self._flap),
            IncludeSVG(self._flap),
            Input(self._flap),
            Include(self._flap),
            MakeIndex(self._flap),
            RequirePackage(self._flap),
            UsePackage(self._flap),
            SubFile(self._flap)
        ]
        self._environments = [
            Overpic(flap),
            Verbatim(flap)
        ]

    def all(self):
        definitions = {}
        for each_macro in self._macros:
            definitions[each_macro.name] = each_macro
        for each_environment in self._environments:
            definitions[each_environment.name] = each_environment
        return definitions

    def create(self, name, parameters, body):
        return Macro(self._flap, name, parameters, body)
