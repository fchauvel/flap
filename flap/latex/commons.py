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


class Context:

    def __init__(self, parent=None, definitions=None):
        self._definitions = definitions or dict()
        self._parent = parent

    def define(self, macro):
        logger.debug("Defining macro {}".format(macro.name))
        self._definitions[macro.name] = macro

    def look_up(self, symbol):
        result = self._definitions.get(symbol, None)
        if not result and self._parent:
            return self._parent.look_up(symbol)
        return result

    @property
    def available_macros(self):
        return list(self._definitions.keys())

    def items(self):
        return self._definitions.items()

    def __setitem__(self, key, value):
        self._definitions[key] = value

    def __getitem__(self, key):
        if self._parent and key not in self._definitions:
            return self._parent[key]
        else:
            return self._definitions.get(key)

    def __contains__(self, key):
        return key in self._definitions or (
            self._parent and key in self._parent)


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
        next_item = self._take()
        if next_item:
            self._cache.append(next_item)
        return next_item

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
        # logger.debug("Taking %s", str(element))
        self._handler(element)
        return element

    def take_while(self, match):
        buffer = []
        while self.look_ahead() and match(self.look_ahead()):
            buffer.append(self.take())
        return buffer

    def take_all(self):
        return self.take_while(lambda e: e is not None)

    def push(self, items):
        if isinstance(items, list):
            assert not any(i is None for i in items), \
                "Cannot push None!"
            self._cache.extend(reversed(items))
        else:
            assert items is not None, \
                "Cannot push None"
            self._cache.append(items)
        logger.debug(f"Pushing! New cache size: {str(len(self._cache))}")
        # self.debug()

    def debug(self):
        logger.debug("View of the stack ...")
        for index in range(len(self._cache)):
            item = self._cache[-(index+1)]
            text = str(item) if isinstance(item, str) else item.as_text
            logger.debug(f"  - {index}: {item}")


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
