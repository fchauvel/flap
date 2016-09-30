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


class TestEndinputRemover(FlapTest):
    """
    Specify the behaviour of the \endinput remover
    """

    def test_endinput_mask_subsequent_content(self):
        self._assume = a_project()\
            .with_main_file("aaa\n"
                            "\\endinput\n"
                            "ccc")

        self._expect = a_project().with_merged_file("aaa\n")

        self._do_test_and_verify()

    def test_endinput_in_a_separate_tex_file(self):
        self._assume = a_project()\
            .with_main_file("aaa\n"
                            "\\input{foo}\n"
                            "ccc")\
            .with_file("foo.tex", ("bbb\n"
                                   "\\endinput\n"
                                   "zzz"))

        self._expect = a_project()\
            .with_merged_file("aaa\n"
                              "bbb\n\n"
                              "ccc")

        self._do_test_and_verify()


class MiscellaneousTests(FlapTest):

    def test_indentation_is_preserved(self):
        self._assume = a_project()\
            .with_main_file("\t\\input{part}")\
            .with_file("part.tex", ("\n"
                                    "\\begin{center}\n"
                                    "\t\\includegraphics[width=4cm]{img/foo}\n"
                                    "  \\includegraphics[width=5cm]{img/foo}\n"
                                    "\\end{center}"))\
            .with_image("img/foo.pdf")

        self._expect = a_project()\
            .with_merged_file("\t\n"
                              "\\begin{center}\n"
                              "\t\\includegraphics[width=4cm]{img_foo}\n"
                              "  \\includegraphics[width=5cm]{img_foo}\n"
                              "\\end{center}")\
            .with_image("img_foo.pdf")

        self._do_test_and_verify()

    def test_conflicting_images_names(self):
        self._assume = a_project()\
            .with_main_file("\\includegraphics[width=\\textwidth]{partA/result}\\n"
                            "\\includegraphics[width=\\textwidth]{partB/result}\\n")\
            .with_image("partA/result.pdf")\
            .with_image("partB/result.pdf")

        self._expect = a_project()\
            .with_merged_file("\\includegraphics[width=\\textwidth]{partA_result}\\n"
                              "\\includegraphics[width=\\textwidth]{partB_result}\\n")\
            .with_image("partA_result.pdf")\
            .with_image("partB_result.pdf")

        self._do_test_and_verify()

    def test_flattening_in_a_file(self):
        self._assume = a_project()\
            .with_main_file("blablabla")

        self._expect = a_project()\
            .with_merged_file("blablabla")

        self._runner._destination = \
            lambda name: self._runner._output_path(name) / "merged.tex"

        self._do_test_and_verify()

    def test_resources_are_copied(self):
        self._assume = a_project()\
            .with_main_file("blablabla")\
            .with_file("style.cls", "class content")

        self._expect = a_project()\
            .with_merged_file("blablabla")\
            .with_file("style.cls", "class content")

        self._do_test_and_verify()

if __name__ == '__main__':
    main()
