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

from flap.latex.macros.commons import Macro


class TexFileInclusion(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)
        self._requires_expansion = True

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("link", parser.capture_one())

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        content = self._flap.content_of(link, invocation)
        if not link.endswith(".tex"):
            link += ".tex"
        return parser._spawn(parser._create.as_tokens(
            content, link), dict()).rewrite()


class Input(TexFileInclusion):
    """
    Intercept the `\\input` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\input")


class Include(TexFileInclusion):
    """
    Intercept the `\\include` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\include")

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        if self._flap.shall_include(link):
            result = super()._execute(parser, invocation)
            return result + parser._create.as_list(r"\clearpage")
        return []


class SubFile(TexFileInclusion):

    def __init__(self, flap):
        super().__init__(flap, r"\subfile")


class EndInput(Macro):

    def __init__(self, flap):
        super().__init__(flap, r"\endinput", None, None)

    def _execute(self, parser, invocation):
        source = invocation.name[0].location.source
        self._flap.end_of_input(source, invocation)
        parser.flush(source)
        return []


class IncludeOnly(Macro):
    """
    Intercept includeonly commands
    """

    def __init__(self, flap):
        super().__init__(flap, r"\includeonly", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("selection", parser.capture_one())

    def _execute(self, parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("selection"))
        files_to_include = list(map(str.strip, text.split(",")))
        self._flap.include_only(files_to_include, invocation)
        return []
