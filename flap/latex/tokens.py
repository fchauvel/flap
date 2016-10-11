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


from flap.latex.symbols import Symbol, SymbolTable


class Token:
    """All the possible tokens recognised by a TeX engine"""

    DISPLAY = "{category}({text})"

    def __init__(self, text, category):
        self._text = text
        self._category = category

    def accept(self, parser):
        if self._category == Symbol.CONTROL:
            parser.invoke_command(self._text)
        else:
            parser.dump(self._text)

    def is_a(self, category):
        return self._category == category

    @property
    def ends_the_text(self):
        return self._category == Symbol.END_OF_TEXT

    @property
    def is_a_character(self):
        return self._category == Symbol.CHARACTER

    @property
    def is_a_parameter(self):
        return self._category == Symbol.PARAMETER

    @property
    def begins_a_group(self):
        return self._category == Symbol.BEGIN_GROUP

    @property
    def is_a_whitespace(self):
        return self._category == Symbol.WHITE_SPACES

    def __eq__(self, other_token):
        if not isinstance(other_token, Token):
            return False
        return self._text == other_token._text \
               and self._category == other_token._category

    def __repr__(self):
        return self.DISPLAY.format(text=self._text, category=self._category.name.lower())

    def __str__(self):
        return self._text


class TokenFactory:

    def __init__(self, symbol_table):
        assert isinstance(symbol_table, SymbolTable)
        self._symbols = symbol_table

    @staticmethod
    def character(text):
        return Token(text, Symbol.CHARACTER)

    @staticmethod
    def command(text):
        return Token(text, Symbol.CONTROL)

    @staticmethod
    def white_space(text):
        return Token(text, Symbol.WHITE_SPACES)

    @staticmethod
    def comment(text):
        return Token(text, Symbol.COMMENT)

    def new_line(self, text=None):
        text = text if text else self._symbols.get(Symbol.NEW_LINE)
        return Token(text, Symbol.NEW_LINE)

    def begin_group(self, text=None):
        text = text if text else self._symbols.get(Symbol.BEGIN_GROUP)
        return Token(text, Symbol.BEGIN_GROUP)

    def end_group(self, text=None):
        text = text if text else self._symbols.get(Symbol.END_GROUP)
        return Token(text, Symbol.END_GROUP)

    def end_of_text(self):
        text = self._symbols.get(Symbol.END_OF_TEXT)
        return Token(text, Symbol.END_OF_TEXT)

    @staticmethod
    def parameter(key):
        return Token(key, Symbol.PARAMETER)

    def math(self):
        text = self._symbols.get(Symbol.MATH)
        return Token(text, Symbol.MATH)

    def superscript(self, text=None):
        text = text if text else self._symbols.get(Symbol.SUPERSCRIPT)
        return Token(text, Symbol.SUPERSCRIPT)

    def subscript(self, text=None):
        text = text if text else self._symbols.get(Symbol.SUBSCRIPT)
        return Token(text, Symbol.SUBSCRIPT)

    def non_breaking_space(self, text=None):
        text = text if text else self._symbols.get(Symbol.NON_BREAKING_SPACE)
        return Token(text, Symbol.NON_BREAKING_SPACE)