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

    def __init__(self, iterable):
        self._characters = iterable

    def look_ahead(self):
        head = self.take()
        self._characters = chain([head], self._characters)
        return head

    @property
    def is_empty(self):
        return self.look_ahead() is None

    def take(self):
        try:
            return next(self._characters)
        except StopIteration:
            return None

    def take_while(self, match):
        buffer = []
        while self.look_ahead() and match(self.look_ahead()):
            buffer.append(self.take())
        return buffer
