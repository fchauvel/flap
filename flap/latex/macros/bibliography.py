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

import re

from flap.latex.macros.commons import Macro, UpdateLink


class Bibliography(UpdateLink):
    """
    Intercept the `\bibliography` directive
    """

    def __init__(self, flap):
        super().__init__(flap, "bibliography")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link_to_bibliography(link, invocation)


class BibliographyStyle(UpdateLink):
    """
    Intercept the `\bibliographystyle` directive
    """

    def __init__(self, flap):
        super().__init__(flap, "bibliographystyle")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link_to_bibliography_style(link, invocation)


class MakeIndex(Macro):
    """
    Intercept 'makeindex' commands. It triggers copying the index style file,
    if they are it can be found locally.
    """

    def __init__(self, flap):
        super().__init__(flap, "makeindex", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.read.options())

    def rewrite2(self, parser, invocation):
        style_file = self._fetch_style_file(parser, invocation)
        new_style_file = self._flap.update_link_to_index_style(
            style_file, invocation)
        return invocation.as_text.replace(style_file, new_style_file)

    @staticmethod
    def _fetch_style_file(parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("options"))
        for each in text.strip()[1:-1].split(","):
            _, value = each.split("=")
            options = re.split(r"(-\w\s)", value)
            for index, _ in enumerate(options):
                if "-s" in options[index]:
                    return options[index + 1]
        return None
