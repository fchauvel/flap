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

from flap.latex.macros.commons import Macro, UpdateLink, Environment


class GraphicsPath(Macro):
    """
    Intercept the `\\graphicspath` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"graphicspath", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument(
            "paths", parser.capture_group())

    def _execute(self, parser, invocation):
        argument = parser.evaluate_as_text(invocation.argument("paths"))
        paths = list(map(str.strip, argument.split(",")))
        self._flap.record_graphic_path(paths, invocation)
        return invocation.as_tokens


class IncludeGraphics(UpdateLink):
    """
    Intercept the `\\includegraphics` directive
    """

    def __init__(self, flap):
        super().__init__(flap, "includegraphics")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link_to_graphic(link, invocation)


class IncludeSVG(UpdateLink):
    """
    Intercept the r`\\includesvg` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"includesvg")

    def update_link(self, parser, link, invocation):
        searched_directories = []
        options = self._extract_options(parser, invocation)
        if self.SVG_PATH in options:
            searched_directories.append(options[self.SVG_PATH])
        return self._flap.update_link_to_graphic(link,
                                                 invocation,
                                                 searched_directories)

    SVG_PATH = "svgpath"

    @staticmethod
    def _extract_options(parser, invocation):
        full_options = parser.evaluate_as_text(
            invocation.argument("options"))
        if not full_options.strip():
            return {}
        result = {}
        options = full_options[1:-1]
        for each_attribute in options.split(","):
            key, value = each_attribute.split("=")
            result[key] = value
        return result


class Overpic(Environment):
    """
    Intercept the \begin{overpic} environment
    """

    def __init__(self, flap):
        super().__init__(flap, "overpic")

    def execute(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("link", parser.capture_one())
        link = parser.evaluate_as_text(invocation.argument("link"))
        new_link = self._flap.update_link_to_graphic(link, invocation)
        return invocation.substitute("link", parser._create.as_list(
            "{" + new_link + "}")).as_tokens
