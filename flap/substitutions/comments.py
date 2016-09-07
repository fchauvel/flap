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

from re import sub
from flap.substitutions.commons import ProcessorDecorator


class CommentsRemover(ProcessorDecorator):
    """
    Remove the comments from the LaTeX source (i.e., replace them by nothing)
    """

    def __init__(self, delegate):
        super().__init__(delegate)

    def fragments(self):
        for each_fragment in self._delegate.fragments():
            without_comments = sub(r"(?<!\\|\|)%(?:[^\n]*)\n", "", each_fragment.text())
            each_fragment._text = without_comments
            yield each_fragment

