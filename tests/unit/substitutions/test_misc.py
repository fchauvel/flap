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


class TestEndinputRemover(FlapUnitTest):
    """
    Specify the behaviour of the Endinput remover
    """

    def test_endinput_mask_subsequent_content(self):
        self.project.root_latex_code = "aaa\n" \
                                       "\\endinput\n" \
                                       "ccc"
        self.run_flap()
        self.verify_merge("aaa\n")

    def test_endinput_in_a_separate_tex_file(self):
        self.project.root_latex_code = "aaa\n" \
                                       "\\input{foo}\n" \
                                       "ccc"

        self.project.parts["foo.tex"] = ("bbb\n"
                                         "bbb\n"
                                         "\\endinput\n"
                                         "zzz")
        self.run_flap()

        self.verify_merge("aaa\n"
                           "bbb\n"
                           "bbb\n\n"
                           "ccc")


class MiscellaneousTests(FlapUnitTest):

    def test_indentation_is_preserved(self):
        self.project.root_latex_code = "\t\\input{part}"
        self.project.parts["part.tex"] = ("\n"
                                          "\\begin{center}\n"
                                          "\t\\includegraphics[width=4cm]{img/foo}\n"
                                          "  \\includegraphics[width=5cm]{img/foo}\n"
                                          "\\end{center}")
        self.project.images = ["img/foo.pdf"]

        self.run_flap()

        self.verify_merge("\t\n"
                          "\\begin{center}\n"
                          "\t\\includegraphics[width=4cm]{img_foo}\n"
                          "  \\includegraphics[width=5cm]{img_foo}\n"
                          "\\end{center}")
        self.verify_image("img_foo.pdf")

    def test_conflicting_images_names(self):
        self.project.root_latex_code = \
            "\\includegraphics[width=\\textwidth]{partA/result}\\n" \
            "\\includegraphics[width=\\textwidth]{partB/result}\\n"

        self.project.images = [
            "partA/result.pdf",
            "partB/result.pdf"]

        self.run_flap()

        self.verify_merge(
            "\\includegraphics[width=\\textwidth]{partA_result}\\n"
            "\\includegraphics[width=\\textwidth]{partB_result}\\n")

        self.verify_image("partA_result.pdf")
        self.verify_image("partB_result.pdf")

    def test_flattening_in_a_file(self):
        self.project.root_latex_code = "blablabla"

        self.run_flap(output="output/root.tex")

        self.verify_merge("blablabla")

    def test_resources_are_copied(self):
        self.project.root_latex_code = "xxx"
        self.project.resources = ["style.cls"]

        self.run_flap()

        self.verify_resources()


if __name__ == '__main__':
    main()
