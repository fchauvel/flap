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

import enum

class Kind(enum.Enum):
    FOO = 4
    BAR = 2


class Bidon:

    def __init__(self):
        self._data = {Kind.FOO: "blablabla"}

    def __getattr__(self, item):
        if item in [each_kind.name for each_kind in list(Kind)]:
            return self._data[Kind[item]]
        return self.__getattribute__(item)

if __name__ == "__main__":
    bidon = Bidon()
    print("Value = ", bidon.FOO)