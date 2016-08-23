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
from tests.unit.engine import FlapUnitTest


class SubfileMergerTests(FlapUnitTest):

    def test_simple_merge(self):
        self.project.root_latex_code = "\\subfile{foo}"

        self.project.parts["foo.tex"] = "\\documentclass[../main.tex]{subfiles}" \
                                        "\\begin{document}" \
                                        "Blahblah blah!\\n" \
                                        "\\end{document}"

        self.run_flap()

        self.verify_merge("Blahblah blah!\\n")

    def test_recursive_merge(self):
        self.project.root_latex_code = "\\subfile{subpart}"

        self.project.parts["subpart.tex"] \
            = "\\documentclass[../main.tex]{subfiles}" \
              "\\begin{document}" \
              "\\subfile{subsubpart}\\n" \
              "\\end{document}"

        self.project.parts["subsubpart.tex"] \
            = "\\documentclass[../main.tex]{subfiles}" \
              "\\begin{document}" \
              "Blahblah blah!\\n" \
              "\\end{document}"

        self.run_flap()

        self.verify_merge("Blahblah blah!\\n\\n")

    def test_does_not_break_document(self):
        self.project.root_latex_code = \
            "\\documentclass{article}\n" \
            "\\usepackage{graphicx}\n" \
            "\\begin{document}\n" \
            "This is my document\n" \
            "\\end{document}\n"

        self.run_flap()

        self.verify_merge(self.project.root_latex_code)

