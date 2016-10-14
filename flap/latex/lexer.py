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

from flap.latex.commons import Stream, Position
from flap.latex.tokens import TokenFactory


class Lexer:
    """
    Scan a stream of character and yields a stream of token. The lexer shall define handler for each category of symbols.
    These handlers are automatically selected using reflection: each handler shall be named "_read_category".
    """

    def __init__(self, symbols):
        self._input = None
        self._symbols = symbols
        self._tokens = TokenFactory(self._symbols)
        self._position = Position(1, 1)

    @property
    def symbols(self):
        return self._symbols

    @property
    def position(self):
        return self._position

    def _take(self):
        return self._input.take()

    @property
    def _next(self):
        return self._input.look_ahead()

    def tokens_from(self, source):
        def on_take(character):
            if character in self._symbols.NEW_LINE:
                self._position = self._position.next_line()
            else:
                self._position = self._position.next_character()

        self._position = Position(1, 0)
        self._input = Stream(iter(source), on_take)
        while self._next is not None:
            yield self._one_token()

    def _one_token(self):
        handler = self._handler_for(self._symbols.category_of(self._next))
        return handler()

    def _handler_for(self, category):
        handler_name = "_read_" + category.name.lower()
        handler = getattr(self, handler_name)
        assert handler, "Lexer has no handler for '%s' symbols" % category.name
        return handler

    def _read_character(self):
        character = self._take()
        return self._tokens.character(self._position, character)

    def _read_control(self):
        marker = self._take()
        location = self._position
        assert marker in self._symbols.CONTROL
        if not self._next.isalpha():
            name = self._take()
        else:
            name = self._take_while(lambda c: c.isalpha())
        return self._tokens.command(location, marker + name)

    def _take_while(self, predicate):
        return "".join(self._input.take_while(predicate))

    def _read_comment(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.COMMENT
        text = self._take_while(lambda c: c not in self._symbols.NEW_LINE)
        return self._tokens.comment(location, marker + text)

    def _read_white_spaces(self):
        marker = self._input.take()
        location = self._position
        spaces = self._take_while(lambda c: c in self._symbols.WHITE_SPACES)
        return self._tokens.white_space(location, marker + spaces)

    def _read_new_line(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.NEW_LINE
        return self._tokens.new_line(location, marker)

    def _read_begin_group(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.BEGIN_GROUP
        return self._tokens.begin_group(location, marker)

    def _read_end_group(self):
        marker = self._take()
        location = self._position
        assert marker in self._symbols.END_GROUP
        return self._tokens.end_group(location, marker)

    def _read_parameter(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.PARAMETER
        text = marker + self._take_while(lambda c: c.isdigit())
        return self._tokens.parameter(location, text)

    def _read_math(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.MATH
        return self._tokens.math(location)

    def _read_superscript(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.SUPERSCRIPT
        return self._tokens.superscript(location, marker)

    def _read_subscript(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.SUBSCRIPT
        return self._tokens.subscript(location, marker)

    def _read_non_breaking_space(self):
        marker = self._input.take()
        location = self._position
        assert marker in self._symbols.NON_BREAKING_SPACE
        return self._tokens.non_breaking_space(location, marker)