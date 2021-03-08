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


class Source:
    """
    A data source, that is a text
    """
    @staticmethod
    def anonymous(text):
        return Source(text, "anonymous")

    @staticmethod
    def with_name(text, name):
        return Source(text, name)

    def __init__(self, content, name="Unknown"):
        self.name = name
        self.content = content


class Stream:
    """
    A stream of characters, on which we can peek.

    One can equip a stream with an event handler that gets triggered
    every times the stream moves forward, that is every time the take
    method is called, directly or indirectly.
    """

    def __init__(self, iterable, handler=lambda x: None):
        assert hasattr(iterable, "__iter__"), \
            "Stream requires an iterable, but found an '%s'!" % (
                type(iterable))
        self._characters = iter(iterable)
        assert callable(handler), \
            "Stream expect a callable hanlder, but found a '%s" % (
                type(handler))
        self._handler = handler
        self._cache = []

    def look_ahead(self):
        self._cache.append(self._take())
        return self._cache[-1]

    @property
    def is_empty(self):
        return self.look_ahead() is None

    def _take(self):
        if self._cache:
            return self._cache.pop()
        try:
            return next(self._characters)
        except StopIteration:
            return None

    def take(self):
        element = self._take()
        self._handler(element)
        return element

    def take_while(self, match):
        buffer = []
        while self.look_ahead() and match(self.look_ahead()):
            buffer.append(self.take())
        return buffer

    def take_all(self):
        return self.take_while(lambda e: e is not None)


class Position:

    UNKNOWN = "Unknown source file"
    REPRESENTATION = "{source} @({line}, {column})"

    def __init__(self, line, column, source=None):
        self._source = source or self.UNKNOWN
        self._line = line
        self._column = column

    @property
    def source(self):
        return self._source

    @property
    def line(self):
        return self._line

    @property
    def column(self):
        return self._column

    def next_line(self):
        return Position(self._line + 1, 0, self._source)

    def next_character(self):
        return Position(self._line, self._column + 1, self._source)

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self._line == other._line and \
            self._column == other._column

    def __repr__(self):
        return self.REPRESENTATION.format(
            source=self._source, line=self._line, column=self._column)
