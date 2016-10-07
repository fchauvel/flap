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

from itertools import chain

from flap.latex.tokens import Token


class Stream:
    """A stream of characters that, on which we can peek"""

    def __init__(self, characters):
        self._characters = iter(characters)

    def peek(self):
        head = self._take()
        self._characters = chain(head, self._characters)
        return head

    def _take(self):
        try:
            return next(self._characters)
        except StopIteration:
            return "\0"

    def take_one(self):
        return self._take()

    def take_while(self, match):
        buffer = ""
        while match(self.peek()):
            buffer += self.take_one()
        return buffer


class Symbols:
    """Define all the characters recognised by the TeX engine"""
    BEGIN_GROUP = ["{"]
    COMMENT = ["%"]
    CONTROL = ["\\"]
    END_GROUP = ["}"]
    END_OF_STRING = ["\0"]
    MATH = ["$"]
    NEW_LINE = ["\n"]
    NON_BREAKING_SPACE = ["~"]
    PARAMETER = ["#"]
    SUBSCRIPT = ["_"]
    SUPERSCRIPT = ["^"]
    WHITE_SPACES = [" ", "\t"]


class Lexer:

    def __init__(self, source):
        self._input = Stream(source)

    def next(self):
        head = self._input.peek()
        while head not in Symbols.END_OF_STRING:
            yield self._one_token()
            head = self._input.peek()

    def _one_token(self):
        head = self._input.peek()
        if head in Symbols.CONTROL:
            return self._read_macro_name()
        elif head in Symbols.COMMENT:
            return self._read_comment()
        elif head in Symbols.WHITE_SPACES:
            return self._read_white_spaces()
        elif head in Symbols.NEW_LINE:
            return self._read_new_line()
        elif head in Symbols.BEGIN_GROUP:
            return self._read_begin_group()
        elif head in Symbols.END_GROUP:
            return self._read_end_group()
        elif head in Symbols.PARAMETER:
            return self._read_parameter()
        elif head in Symbols.MATH:
            return self._read_math()
        elif head in Symbols.SUPERSCRIPT:
            return self._read_superscript()
        elif head in Symbols.SUBSCRIPT:
            return self._read_subscript()
        elif head in Symbols.NON_BREAKING_SPACE:
            return self._read_non_breaking_space()
        else:
            return Token.character(self._input.take_one())

    def _read_macro_name(self):
        assert self._input.take_one() in Symbols.CONTROL
        if not self._input.peek().isalpha():
            name = self._input.take_one()
        else:
            name = self._input.take_while(lambda c: c.isalpha())
        return Token.command(name)

    def _read_comment(self):
        assert self._input.take_one() in Symbols.COMMENT
        text = self._input.take_while(lambda c: c not in Symbols.NEW_LINE + Symbols.END_OF_STRING)
        return Token.comment(text)

    def _read_white_spaces(self):
        self._input.take_while(lambda c: c in Symbols.WHITE_SPACES)
        return Token.white_space()

    def _read_new_line(self):
        assert self._input.take_one() in Symbols.NEW_LINE
        return Token.new_line()

    def _read_begin_group(self):
        self._input.take_one()
        return Token.begin_group()

    def _read_end_group(self):
        self._input.take_one()
        return Token.end_group()

    def _read_parameter(self):
        assert self._input.take_one() in Symbols.PARAMETER
        key = self._input.take_while(lambda c: c.isdigit())
        return Token.parameter(key)

    def _read_math(self):
        assert self._input.take_one() in Symbols.MATH
        return Token.math()

    def _read_superscript(self):
        assert self._input.take_one() in Symbols.SUPERSCRIPT
        return Token.superscript()

    def _read_subscript(self):
        assert self._input.take_one() in Symbols.SUBSCRIPT
        return Token.subscript()

    def _read_non_breaking_space(self):
        assert self._input.take_one() in Symbols.NON_BREAKING_SPACE
        return Token.non_breaking_space()