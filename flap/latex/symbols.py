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

from flap import logger
from enum import Enum, unique


@unique
class Symbol(Enum):
    """
    Define the categories of character as specified  by TeX.

    See https://en.wikibooks.org/wiki/TeX/catcode
    """
    CONTROL = 0
    BEGIN_GROUP = 1
    END_GROUP = 2
    MATH = 3
    ALIGNMENT_TAB = 4
    NEW_LINE = 5
    PARAMETER = 6
    SUPERSCRIPT = 7
    SUBSCRIPT = 8
    IGNORED = 9
    WHITE_SPACES = 10
    CHARACTER = 11
    OTHERS = 12
    NON_BREAKING_SPACE = 13
    COMMENT = 14
    INVALID = 15
    END_OF_TEXT = 16


class SymbolTable:
    """
    Characters recognised by (La)TeX, augmented with some relevant for
    parsing such new lines.
    """

    @staticmethod
    def character_range(start, end):
        return [chr(code) for code in range(ord(start), ord(end) + 1)]

    @staticmethod
    def default():
        return SymbolTable({
            Symbol.BEGIN_GROUP: ["{"],
            Symbol.CHARACTER: SymbolTable.character_range('a', 'z') +
            SymbolTable.character_range('A', 'Z'),
            Symbol.COMMENT: ["%"],
            Symbol.CONTROL: ["\\"],
            Symbol.END_GROUP: ["}"],
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

    def clone(self):
        categories = {each_category: each_characters.copy()
                      for each_category, each_characters
                      in self._symbols.items()}
        return SymbolTable(categories)

    def assign(self, character, category_code):
        assert isinstance(character, str), \
            "Need character as a string, but got {}".format(
                type(character))
        assert len(character) == 1, \
            "Need a single character, but got '{}'".format(character)
        assert isinstance(category_code, int), \
            "Expect category as an integer, but got {}".format(
                type(category_code))
        self._remove(character)
        category = Symbol(category_code)
        if category != Symbol.OTHERS:
            self._symbols[category].append(character)

        # logger.debug("Character table:")
        # for category, characters in self._symbols.items():
        #   logger.debug("{}: {}".format(category, ",".join(characters)))


    def _remove(self, character):
        for any_category in self._symbols:
            if character in self._symbols[any_category]:
                self._symbols[any_category].remove(character)
                return
        # Else we do nothing, is the character belongs to OTHER, but
        # there is no need to remove it. OTHER is only the default

    def __getitem__(self, key):
        assert key in list(
            Symbol), "Symbol table only maps symbol categories to symbol lists"
        return self._symbols.get(key, [])

    def __setitem__(self, key, value):
        assert key in list(
            Symbol), "Symbol table only maps symbol categories to symbol lists"
        self._symbols[key] = value

    def match(self, character, category):
        return character in self._symbols[category]

    def category_of(self, character):
        for category, markers in self._symbols.items():
            if character in markers:
                return category
        return Symbol.OTHERS

    @property
    def end_of_text(self):
        return self.get(Symbol.END_OF_TEXT)

    def get(self, category):
        return self._symbols[category][0]

    def __getattr__(self, item):
        """
        Expose the entries of the internal _tokens dictionary as attributes.

        With this, we access the list of character defined for one category
        >>> table = SymbolTable.default()
        >>> table.CHARACTER

        instead of:
        >>> table[Symbol.CHARACTER]
        """
        if item in [each.name for each in list(Symbol)]:
            return self._symbols[Symbol[item]]
        return self.__getattribute__(item)
