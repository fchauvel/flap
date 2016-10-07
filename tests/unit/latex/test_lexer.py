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

    def test_recognises_a_single_character(self):
        self._lexer = Lexer("b")
        self._verify_tokens(Token.character("b"))

    def test_recognises_a_single_command(self):
        self._lexer = Lexer(r"\myMacro")
        self._verify_tokens(Token.command("myMacro"))

    def test_recognises_a_single_special_character_command(self):
        self._lexer = Lexer(r"\%")
        self._verify_tokens(Token.command("%"))

    def test_recognises_sequences_of_single_character_command(self):
        self._lexer = Lexer(r"\%\$\\")
        self._verify_tokens(Token.command("%"),
                            Token.command("$"),
                            Token.command("\\"))

    def test_recognises_two_commands(self):
        self._lexer = Lexer(r"\def\foo")
        self._verify_tokens(Token.command("def"),
                            Token.command("foo"))

    def test_recognises_two_commands_separated_by_white_spaces(self):
        self._lexer = Lexer("\\def  \t  \\foo")
        self._verify_tokens(Token.command("def"),
                            Token.white_space(),
                            Token.command("foo"))

    def test_recognises_a_comment(self):
        self._lexer = Lexer("%This is a comment\n\\def\\foo")
        self._verify_tokens(Token.comment("This is a comment"),
                            Token.new_line(),
                            Token.command("def"),
                            Token.command("foo"))

    def test_recognises_an_opening_group(self):
        self._lexer = Lexer("{")
        self._verify_tokens(Token.begin_group())

    def test_recognises_an_ending_group(self):
        self._lexer = Lexer("}")
        self._verify_tokens(Token.end_group())

    def test_recognises_an_parameter(self):
        self._lexer = Lexer("\def#1")
        self._verify_tokens(Token.command("def"),
                            Token.parameter("1"))

    def test_recognises_a_complete_macro_definition(self):
        self._lexer = Lexer("\\def\\point#1#2{(#2,#1)}")
        self._verify_tokens(Token.command("def"),
                            Token.command("point"),
                            Token.parameter("1"),
                            Token.parameter("2"),
                            Token.begin_group(),
                            Token.character("("),
                            Token.parameter("2"),
                            Token.character(","),
                            Token.parameter("1"),
                            Token.character(")"),
                            Token.end_group())

    def test_recognises_math_mode(self):
        self._lexer = Lexer("$")
        self._verify_tokens(Token.math())

    def test_recognises_superscript(self):
        self._lexer = Lexer("^")
        self._verify_tokens(Token.superscript())

    def test_recognises_subscript(self):
        self._lexer = Lexer("_")
        self._verify_tokens(Token.subscript())

    def test_recognises_non_breaking_space(self):
        self._lexer = Lexer("~")
        self._verify_tokens(Token.non_breaking_space())

    def _verify_tokens(self, *expected_tokens):
        assert self._lexer, "The lexer should be defined first!"
        actual_tokens = list(self._lexer.next())
        self.assertListEqual(list(expected_tokens), actual_tokens)


if __name__ == "__main__":
    main()