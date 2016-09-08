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

from unittest import main
from tests.unit.engine import FlapUnitTest


class BibliographyTests(FlapUnitTest):

    def test_fetching_bibliography(self):
        self.project.root_latex_code = "\\bibliography{biblio}"

        self.project.images = ["biblio.bib"]

        self.run_flap()

        self.verify_merge("\\bibliography{biblio}")
        self.verify_image("biblio.bib")

    def test_fetching_bibliography_stored_in_sub_directories(self):
        self.project.root_latex_code = "\\bibliography{parts/biblio}"

        self.project.images = ["parts/biblio.bib"]

        self.run_flap()

        self.verify_merge("\\bibliography{parts_biblio}")
        self.verify_image("parts_biblio.bib")

    def test_interaction_with_graphicpath(self):
        self.project.root_latex_code = "\\graphicspath{img}" \
                                       "\\bibliography{parts/biblio}"

        self.project.images = ["parts/biblio.bib"]

        self.run_flap()

        self.verify_merge("\\bibliography{parts_biblio}")
        self.verify_image("parts_biblio.bib")


if __name__ == '__main__':
    main()
