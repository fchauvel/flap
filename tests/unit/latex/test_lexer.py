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

from flap.latex.lexer import Lexer
from flap.latex.tokens import Token


class LexerTests(TestCase):

    def setUp(self):
        self._lexer = Lexer()
        self._text = None

    def test_recognises_a_single_character(self):
        self._text = "b"
        self._verify_tokens(Token.character("b"))

    def test_recognises_a_single_command(self):
        self._text = r"\myMacro"
        self._verify_tokens(Token.command(r"\myMacro"))

    def test_recognises_a_single_special_character_command(self):
        self._text = r"\%"
        self._verify_tokens(Token.command(r"\%"))

    def test_recognises_sequences_of_single_character_command(self):
        self._text = r"\%\$\\"
        self._verify_tokens(Token.command(r"\%"),
                            Token.command(r"\$"),
                            Token.command(r"\\"))

    def test_recognises_two_commands(self):
        self._text = r"\def\foo"
        self._verify_tokens(Token.command(r"\def"),
                            Token.command(r"\foo"))

    def test_recognises_two_commands_separated_by_white_spaces(self):
        self._text = "\\def  \t  \\foo"
        self._verify_tokens(Token.command(r"\def"),
                            Token.white_space("  \t  "),
                            Token.command(r"\foo"))

    def test_recognises_a_comment(self):
        self._text = "%This is a comment\n\\def\\foo"
        self._verify_tokens(Token.comment("%This is a comment"),
                            Token.new_line("\n"),
                            Token.command(r"\def"),
                            Token.command(r"\foo"))

    def test_recognises_an_opening_group(self):
        self._text = "{"
        self._verify_tokens(Token.begin_group())

    def test_recognises_an_ending_group(self):
        self._text = "}"
        self._verify_tokens(Token.end_group())

    def test_recognises_an_parameter(self):
        self._text = "\def#1"
        self._verify_tokens(Token.command(r"\def"),
                            Token.parameter("#1"))

    def test_recognises_a_complete_macro_definition(self):
        self._text = "\\def\\point#1#2{(#2,#1)}"
        self._verify_tokens(Token.command(r"\def"),
                            Token.command(r"\point"),
                            Token.parameter("#1"),
                            Token.parameter("#2"),
                            Token.begin_group("{"),
                            Token.character("("),
                            Token.parameter("#2"),
                            Token.character(","),
                            Token.parameter("#1"),
                            Token.character(")"),
                            Token.end_group("}"))

    def test_recognises_math_mode(self):
        self._text = "$"
        self._verify_tokens(Token.math())

    def test_recognises_superscript(self):
        self._text = "^"
        self._verify_tokens(Token.superscript())

    def test_recognises_subscript(self):
        self._text = "_"
        self._verify_tokens(Token.subscript())

    def test_recognises_non_breaking_space(self):
        self._text = "~"
        self._verify_tokens(Token.non_breaking_space())

    def _verify_tokens(self, *expected_tokens):
        assert self._lexer, "The lexer should be defined first!"
        actual_tokens = list(self._lexer.tokens_from(self._text))
        self.assertListEqual(list(expected_tokens), actual_tokens)


if __name__ == "__main__":
    main()