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

from flap.latex.lexer import Lexer, SymbolTable
from flap.latex.tokens import Token


class LexerTests(TestCase):

    def setUp(self):
        self._symbols = SymbolTable.default()
        self._lexer = Lexer(self._symbols)
        self._text = None

    def test_recognises_a_single_character(self):
        self._text = "b"
        self._verify_tokens(self._symbols.character("b"))

    def test_recognises_a_single_command(self):
        self._text = r"\myMacro"
        self._verify_tokens(self._symbols.command(r"\myMacro"))

    def test_recognises_a_single_special_character_command(self):
        self._text = r"\%"
        self._verify_tokens(self._symbols.command(r"\%"))

    def test_recognises_sequences_of_single_character_command(self):
        self._text = r"\%\$\\"
        self._verify_tokens(self._symbols.command(r"\%"),
                            self._symbols.command(r"\$"),
                            self._symbols.command(r"\\"))

    def test_recognises_two_commands(self):
        self._text = r"\def\foo"
        self._verify_tokens(self._symbols.command(r"\def"),
                            self._symbols.command(r"\foo"))

    def test_recognises_two_commands_separated_by_white_spaces(self):
        self._text = "\\def  \t  \\foo"
        self._verify_tokens(self._symbols.command(r"\def"),
                            self._symbols.white_space("  \t  "),
                            self._symbols.command(r"\foo"))

    def test_recognises_a_comment(self):
        self._text = "%This is a comment\n\\def\\foo"
        self._verify_tokens(self._symbols.comment("%This is a comment"),
                            self._symbols.new_line(),
                            self._symbols.command(r"\def"),
                            self._symbols.command(r"\foo"))

    def test_recognises_an_opening_group(self):
        self._text = "{"
        self._verify_tokens(self._symbols.begin_group())

    def test_recognises_an_ending_group(self):
        self._text = "}"
        self._verify_tokens(self._symbols.end_group())

    def test_recognises_an_parameter(self):
        self._text = "\def#1"
        self._verify_tokens(self._symbols.command(r"\def"),
                            self._symbols.parameter("#1"))

    def test_recognises_a_complete_macro_definition(self):
        self._text = "\\def\\point#1#2{(#2,#1)}"
        self._verify_tokens(self._symbols.command(r"\def"),
                            self._symbols.command(r"\point"),
                            self._symbols.parameter("#1"),
                            self._symbols.parameter("#2"),
                            self._symbols.begin_group(),
                            self._symbols.character("("),
                            self._symbols.parameter("#2"),
                            self._symbols.character(","),
                            self._symbols.parameter("#1"),
                            self._symbols.character(")"),
                            self._symbols.end_group())

    def test_recognises_math_mode(self):
        self._text = "$"
        self._verify_tokens(self._symbols.math())

    def test_recognises_superscript(self):
        self._text = "^"
        self._verify_tokens(self._symbols.superscript())

    def test_recognises_subscript(self):
        self._text = "_"
        self._verify_tokens(self._symbols.subscript())

    def test_recognises_non_breaking_space(self):
        self._text = "~"
        self._verify_tokens(self._symbols.non_breaking_space())

    def _verify_tokens(self, *expected_tokens):
        assert self._lexer, "The lexer should be defined first!"
        actual_tokens = list(self._lexer.tokens_from(self._text))
        self.assertListEqual(list(expected_tokens), actual_tokens)


if __name__ == "__main__":
    main()