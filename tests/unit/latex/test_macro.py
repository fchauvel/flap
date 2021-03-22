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

from unittest import TestCase, main

from flap.latex.macros.commons import Invocation


class InvocationTests(TestCase):

    def setUp(self):
        self._name = "foo"
        self._invocation = Invocation("foo")

    def test_name_definition(self):
        self._invocation.name = self._name
        self.assertEqual(self._name, self._invocation.name)

    def test_defining_named_arguments(self):
        self._invocation.append_argument("bar", ["a", "b", "c"])
        self.assertEqual(["a", "b", "c"], self._invocation.argument("bar"))

    def test_as_text(self):
        self._invocation.name = [r"\foo"]
        self._invocation.append_argument(
            "options", [each for each in "[this is a text]"])
        self._invocation.append(["-", "---"])
        self._invocation.append_argument(
            "link", [each for each in "{link/to/a/file.tex}"])
        self.assertEqual(
            r"\foo[this is a text]----{link/to/a/file.tex}",
            self._invocation.as_text)

    def test_conversion_to_token_list(self):
        self._invocation.name = [r"\foo"]
        self._invocation.append_argument(
            "options", [each for each in "[this is a text]"])
        self._invocation.append([each for each in "----"])
        self._invocation.append_argument(
            "link", [each for each in "{link/to/a/file.tex}"])
        self.assertEqual([r"\foo"] +
                         [each for each in "[this is a text]"] +
                         [each for each in "----"] +
                         [each for each in "{link/to/a/file.tex}"],
                         self._invocation.as_tokens)

    def test_iterating_over_items(self):
        self._invocation.name = r"\foo"
        self._invocation.append_argument("options", "this is a text")
        self._invocation.append("----")
        self._invocation.append_argument("link", "{link/to/a/file.tex}")
        self.assertEqual({"options": "this is a text",
                          "link": "{link/to/a/file.tex}"},
                         self._invocation.arguments)

    def test_argument_substitution(self):
        self._invocation.name = r"\foo"
        self._invocation.append_argument("text", ["z", "y", "x"])
        self.assertEqual(
            "bar", self._invocation.substitute(
                "text", "bar").arguments["text"])

    def test_argument(self):
        self._invocation.name = [r"\foo"]
        self._invocation.append_argument("link", ["p1", ",", "p2"])
        self.assertEqual([r"\foo"], self._invocation.name)


if __name__ == "__main__":
    main()
