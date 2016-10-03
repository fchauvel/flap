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

import re
from flap.substitutions.commons import LinkSubstitution


class Bibliography(LinkSubstitution):
    """
    Detects "\bibliography". When one is detected, it produces a new fragment
    where the link to the file is corrected.
    """

    def __init__(self, delegate, flap):
        super().__init__(delegate, flap)

    def prepare_pattern(self):
        return re.compile(r"\\bibliography\s*(?:\[(?:[^\]]+)\])*\{([^\}]+)\}")

    def find(self, fragment, reference):
        return self.flap.find_resource(fragment, reference, self.extensions_by_priority())

    def extensions_by_priority(self):
        return ["bib"]

    def notify(self, fragment, graphic):
        return self.flap.on_include_graphics(fragment, graphic)
