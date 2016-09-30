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
from tests.commons import FlapTest
from tests.latex_project import a_project


class BibliographyTests(FlapTest):

    def test_fetching_bibliography(self):
        self._assume = a_project()\
            .with_main_file("\\bibliography{biblio}")\
            .with_file("biblio.bib", "some refereneces")

        self._expect = a_project()\
            .with_merged_file("\\bibliography{biblio}")\
            .with_file("biblio.bib", "some refereneces")

        self._do_test_and_verify()

    def test_fetching_bibliography_stored_in_sub_directories(self):
        self._assume = a_project()\
            .with_main_file("\\bibliography{etc/biblio}")\
            .with_file("etc/biblio.bib", "some refereneces")

        self._expect = a_project()\
            .with_merged_file("\\bibliography{etc_biblio}")\
            .with_file("etc_biblio.bib", "some refereneces")

        self._do_test_and_verify()

    def test_interaction_with_graphicpath(self):
        self._assume = a_project()\
            .with_main_file("\\graphicspath{img}"
                            "\\bibliography{parts/biblio}")\
            .with_file("parts/biblio.bib", "some refereneces")

        self._expect = a_project()\
            .with_merged_file("\\bibliography{parts_biblio}")\
            .with_file("parts_biblio.bib", "some refereneces")

        self._do_test_and_verify()


if __name__ == '__main__':
    main()
