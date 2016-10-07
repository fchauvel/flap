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

from enum import Enum


class TokenCategory(Enum):
    """The 12 categories of tokens recognised by a TeX engine"""
    BEGIN_GROUP = 1
    CHARACTER = 2
    COMMAND = 3
    COMMENT = 4
    END_GROUP = 5
    MATH = 6
    NEW_LINE = 7
    NON_BREAKING_SPACE = 8
    PARAMETER = 9
    SUBSCRIPT = 10
    SUPERSCRIPT = 11
    WHITE_SPACE = 12


class Token:
    """All the possible tokens recognised by a TeX engine"""

    DISPLAY = "{category}({text})"

    @staticmethod
    def character(text):
        return Token(text, TokenCategory.CHARACTER)

    @staticmethod
    def command(text):
        return Token(text, TokenCategory.COMMAND)

    @staticmethod
    def white_space():
        return Token(None, TokenCategory.WHITE_SPACE)

    @staticmethod
    def comment(text):
        return Token(text, TokenCategory.COMMENT)

    @staticmethod
    def new_line():
        return Token(None, TokenCategory.NEW_LINE)

    @staticmethod
    def begin_group():
        return Token(None, TokenCategory.BEGIN_GROUP)

    @staticmethod
    def end_group():
        return Token(None, TokenCategory.END_GROUP)

    @staticmethod
    def parameter(key):
        return Token(key, TokenCategory.PARAMETER)

    @staticmethod
    def math():
        return Token(None, TokenCategory.MATH)

    @staticmethod
    def superscript():
        return Token(None, TokenCategory.SUPERSCRIPT)

    @staticmethod
    def subscript():
        return Token(None, TokenCategory.SUBSCRIPT)

    @staticmethod
    def non_breaking_space():
        return Token(None, TokenCategory.NON_BREAKING_SPACE)

    def __init__(self, text, category):
        self._text = text
        self._category = category

    def __eq__(self, other_token):
        if not isinstance(other_token, Token):
            return False
        return self._text == other_token._text \
               and self._category == other_token._category

    def __repr__(self):
        return self.DISPLAY.format(text=self._text, category=self._category.name.lower())