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


class Environment:
    """
    Represent LaTeX environments, such as \begin{center} for instance.
    """

    def __init__(self, flap, name):
        self._flap = flap
        self._name = name

    @property
    def name(self):
        return self._name

    def execute(self, parser, invocation):
        return None


class Overpic(Environment):

    def __init__(self, flap):
        super().__init__(flap, "overpic")

    def execute(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("link", parser.capture_one())
        link = parser.evaluate_as_text(invocation.argument("link"))
        new_link = self._flap.update_link(link, invocation)
        return invocation.substitute("link", parser._create.as_list(
            "{" + new_link + "}")).as_tokens


class Verbatim(Environment):
    """

    """

    def __init__(self, flap):
        super().__init__(flap, "verbatim")

    def execute(self, parser, invocation):
        return parser._create.as_list(
            r"\begin{verbatim}") + parser.capture_until_text(r"\end{verbatim}")