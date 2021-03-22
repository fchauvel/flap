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

from flap import logger
from flap.latex.macros.commons import Macro


class TexFileInclusion(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)
        self._requires_expansion = True

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("link", parser.read.one())

    def execute2(self, parser, invocation):
        self._called = True
        logger.debug("Setting CALLED on %d", id(self))
        link = parser.evaluate_as_text(invocation.argument("link"))
        content = self._flap.content_of(link, invocation)
        logger.debug("TEX INCLUSION %s: '%s'", link, content)
        if not link.endswith(".tex"):
            link += ".tex"
        tokens = parser._create.as_list(content)
        return parser._tokens.push(tokens)

    def rewrite2(self, parser, invocation):
        return []


class Input(TexFileInclusion):
    """
    Intercept the `\\input` directive
    """

    def __init__(self, flap):
        super().__init__(flap, "input")


class Include(TexFileInclusion):
    """
    Intercept the `\\include` directive
    """

    def __init__(self, flap):
        super().__init__(flap, "include")

    def execute2(self, parser, invocation):
        self._called = True
        link = parser.evaluate_as_text(invocation.argument("link"))
        if self._flap.shall_include(link):
            tokens = parser._create.as_list(r"\clearpage")
            parser._tokens.push(tokens)
            super().execute2(parser, invocation)

    def rewrite2(self, parser, invocation):
        return []


class SubFile(TexFileInclusion):

    def __init__(self, flap):
        super().__init__(flap, "subfile")


class EndInput(Macro):

    def __init__(self, flap):
        super().__init__(flap, "endinput", None, None)

    def execute2(self, parser, invocation):
        source = invocation.name.location.source
        self._flap.end_of_input(source, invocation)
        parser.flush(source)

    def rewrite2(self, parser, invocation):
        return []


class IncludeOnly(Macro):
    """
    Intercept includeonly commands
    """

    def __init__(self, flap):
        super().__init__(flap, r"includeonly", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("selection", parser.read.one())

    def execute2(self, parser, invocation):
        pass

    def rewrite2(self, parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("selection"))
        files_to_include = list(map(str.strip, text.split(",")))
        self._flap.include_only(files_to_include, invocation)
        return []
