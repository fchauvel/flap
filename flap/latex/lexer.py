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
from enum import Enum
from flap.latex.tokens import Token, TokenCategory


class Stream:
    """A stream of characters, on which we can peek"""

    def __init__(self, iterable, end_marker):
        self._characters = iterable
        self._end_marker = end_marker

    def look_ahead(self):
        head = self.take()
        self._characters = chain([head], self._characters)
        return head

    def take(self):
        try:
            return next(self._characters)
        except StopIteration:
            return self._end_marker

    def take_while(self, match):
        buffer = ""
        while match(self.look_ahead()):
            buffer += str(self.take())
        return buffer


class Symbol(Enum):
    CHARACTER = 0
    BEGIN_GROUP = 1
    COMMENT = 2
    CONTROL = 3
    END_GROUP = 4
    END_OF_TEXT = 5
    MATH = 6
    NEW_LINE = 7
    NON_BREAKING_SPACE = 8
    PARAMETER = 9
    SUBSCRIPT = 10
    SUPERSCRIPT = 11
    WHITE_SPACES = 12


class SymbolTable:
    """
    Characters recognised by (La)TeX, augmented with some relevant for parsing such new lines.
    """

    @staticmethod
    def default():
        return SymbolTable({
            Symbol.BEGIN_GROUP: ["{"],
            Symbol.COMMENT: ["%"],
            Symbol.CONTROL: ["\\"],
            Symbol.END_GROUP: ["}"],
            Symbol.END_OF_TEXT: ["\0"],
            Symbol.MATH: ["$"],
            Symbol.NEW_LINE: ["\n"],
            Symbol.NON_BREAKING_SPACE: ["~"],
            Symbol.PARAMETER: ["#"],
            Symbol.SUBSCRIPT: ["_"],
            Symbol.SUPERSCRIPT: ["^"],
            Symbol.WHITE_SPACES: [" ", "\t"]
        })

    def __init__(self, symbols):
        self._symbols = symbols

    def __getitem__(self, key):
        assert key in list(Symbol), "Symbol table only maps symbol categories to symbol lists"
        return self._symbols[key]

    def __setitem__(self, key, value):
        assert key in list(Symbol), "Symbol table only maps symbol categories to symbol lists"
        self._symbols[key] = value

    def match(self, character, category):
        return character in self._symbols[category]

    def category_of(self, character):
        for category, markers in self._symbols.items():
            if character in markers:
                return category
        return Symbol.CHARACTER

    def get(self, category):
        return self._symbols[category][0]

    @staticmethod
    def character(text):
        return Token(text, TokenCategory.CHARACTER)

    @staticmethod
    def command(text):
        return Token(text, TokenCategory.COMMAND)

    @staticmethod
    def white_space(text):
        return Token(text, TokenCategory.WHITE_SPACE)

    @staticmethod
    def comment(text):
        return Token(text, TokenCategory.COMMENT)

    def new_line(self, text=None):
        text = text if text else self.get(Symbol.NEW_LINE)
        return Token(text, TokenCategory.NEW_LINE)

    def begin_group(self, text=None):
        text = text if text else self.get(Symbol.BEGIN_GROUP)
        return Token(text, TokenCategory.BEGIN_GROUP)

    def end_group(self, text=None):
        text = text if text else self.get(Symbol.END_GROUP)
        return Token(text, TokenCategory.END_GROUP)

    def end_of_text(self):
        text = self.get(Symbol.END_OF_TEXT)
        return Token(text, TokenCategory.END_OF_TEXT)

    @staticmethod
    def parameter(key):
        return Token(key, TokenCategory.PARAMETER)

    def math(self):
        text = self.get(Symbol.MATH)
        return Token(text, TokenCategory.MATH)

    def superscript(self, text=None):
        text = text if text else self.get(Symbol.SUPERSCRIPT)
        return Token(text, TokenCategory.SUPERSCRIPT)

    def subscript(self, text=None):
        text = text if text else self.get(Symbol.SUBSCRIPT)
        return Token(text, TokenCategory.SUBSCRIPT)

    def non_breaking_space(self, text=None):
        text = text if text else self.get(Symbol.NON_BREAKING_SPACE)
        return Token(text, TokenCategory.NON_BREAKING_SPACE)


class Lexer:
    """
    Scan a stream of character and yields a stream of token. The lexer shall define handler for each category of symbols.
    These handlers are automatically selected using reflection: each handler shall be named "_read_category".
    """

    def __init__(self, symbols):
        self._input = None
        self._symbols = symbols

    @property
    def symbols(self):
        return self._symbols

    def tokens_from(self, source):
        self._input = Stream(iter(source), self._symbols.get(Symbol.END_OF_TEXT))
        head = self._input.look_ahead()
        while not self._match(head, Symbol.END_OF_TEXT):
            yield self._one_token()
            head = self._input.look_ahead()

    def _match(self, character, *categories):
        return any((self._symbols.match(character, any_category) for any_category in categories))

    def _one_token(self):
        head = self._input.look_ahead()
        handler = self._handler_for(self._symbols.category_of(head))
        return handler()

    def _handler_for(self, category):
        handler_name = "_read_" + category.name.lower()
        handler = getattr(self, handler_name)
        assert handler, "Lexer has no handler for '%s' symbols" % category.name
        return handler

    def _read_character(self):
        return self._symbols.character(self._input.take())

    def _read_control(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.CONTROL)
        if not self._input.look_ahead().isalpha():
            name = self._input.take()
        else:
            name = self._input.take_while(lambda c: c.isalpha())
        return self._symbols.command(marker + name)

    def _read_comment(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.COMMENT)
        text = self._input.take_while(lambda c: not self._match(c, Symbol.NEW_LINE, Symbol.END_OF_TEXT))
        return self._symbols.comment(marker + text)

    def _read_white_spaces(self):
        spaces = self._input.take_while(lambda c: self._match(c, Symbol.WHITE_SPACES))
        return self._symbols.white_space(spaces)

    def _read_new_line(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.NEW_LINE)
        return self._symbols.new_line(marker)

    def _read_begin_group(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.BEGIN_GROUP)
        return self._symbols.begin_group(marker)

    def _read_end_group(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.END_GROUP)
        return self._symbols.end_group(marker)

    def _read_parameter(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.PARAMETER)
        key = marker + self._input.take_while(lambda c: c.isdigit())
        return self._symbols.parameter(key)

    def _read_math(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.MATH)
        return self._symbols.math()

    def _read_superscript(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.SUPERSCRIPT)
        return self._symbols.superscript(marker)

    def _read_subscript(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.SUBSCRIPT)
        return self._symbols.subscript(marker)

    def _read_non_breaking_space(self):
        marker = self._input.take()
        assert self._match(marker, Symbol.NON_BREAKING_SPACE)
        return self._symbols.non_breaking_space(marker)