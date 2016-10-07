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

from io import StringIO
from unittest import TestCase, main
from mock import MagicMock

from flap.latex.lexer import Lexer
from flap.latex.parser import Parser


class ParserTests(TestCase):

    def setUp(self):
        self._output = StringIO()
        self._engine = MagicMock()
        self._parser = Parser(Lexer(), self._output, self._engine)

    def test_parsing_a_regular_word(self):
        self._do_test_with("hello", "hello")

    def test_parsing_another_regular_word(self):
        self._do_test_with("bonjour", "bonjour")

    def test_parsing_a_command(self):
        self._do_test_with(r"this is a \macro", r"this is a \macro")

    def test_parsing_a_macro_definition(self):
        self._do_test_with(r"\def\myMacro#1{my #1} \myMacro{some text here}",
                           r"\def\myMacro#1{my #1} \myMacro{some text here}")

    def test_parsing_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\input my-file",
                           r"File content")
        self._engine.content_of.assert_called_once_with("my-file")

    def test_parsing_commented_out_input(self):
        self._do_test_with(r"% \input my-file",
                           r"% \input my-file")
        self._engine.content_of.assert_not_called()

    def _do_test_with(self, input, output):
        self._parser.parse(input)
        self._verify_output_is(output)

    def _verify_output_is(self, expected_text):
        self.assertEqual(expected_text, self._output.getvalue())


if __name__ == '__main__':
    main()
