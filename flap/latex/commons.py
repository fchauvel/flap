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
