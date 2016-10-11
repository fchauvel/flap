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
    END_OF_TEXT = 6
    MATH = 7
    NEW_LINE = 8
    NON_BREAKING_SPACE = 9
    PARAMETER = 10
    SUBSCRIPT = 11
    SUPERSCRIPT = 12
    WHITE_SPACE = 13


class Token:
    """All the possible tokens recognised by a TeX engine"""

    DISPLAY = "{category}({text})"

    def __init__(self, text, category):
        self._text = text
        self._category = category

    def accept(self, parser):
        if self._category == TokenCategory.COMMAND:
            parser.invoke_command(self._text)
        else:
            parser.dump(self._text)

    def is_a(self, category):
        return self._category == category

    def __eq__(self, other_token):
        if not isinstance(other_token, Token):
            return False
        return self._text == other_token._text \
               and self._category == other_token._category

    def __repr__(self):
        return self.DISPLAY.format(text=self._text, category=self._category.name.lower())

    def __str__(self):
        return self._text