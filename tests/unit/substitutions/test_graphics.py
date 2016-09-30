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

from flap.engine import GraphicNotFound
from flap.util.path import Path
from tests.commons import FlapTest, a_project


class GraphicPathTest(FlapTest):

    def test_graphic_are_adjusted_accordingly(self):
        self._assume = a_project()\
            .with_main_file("\\graphicspath{img/}"
                            "blabla"
                            "\\includegraphics[witdh=5cm]{plot}"
                            "blabla")\
            .with_image("img/plot.pdf")

        self._expect = a_project()\
            .with_merged_file("blabla"
                              "\\includegraphics[witdh=5cm]{img_plot}"
                              "blabla")\
            .with_image("img_plot.pdf")

        self._do_test_and_verify()

    def test_escaped_graphicpath(self):
        self._assume = a_project()\
            .with_main_file("\\graphicspath{{./img/}}" \
                            "blabla" \
                            "\\includegraphics[witdh=5cm]{plot}" \
                            "blabla")\
            .with_image("img/plot.pdf")

        self._expect = a_project()\
            .with_merged_file("blabla" \
                              "\\includegraphics[witdh=5cm]{img_plot}" \
                              "blabla")\
            .with_image("img_plot.pdf")

        self._do_test_and_verify()


class IncludeGraphicsProcessorTest(FlapTest):

    def test_links_to_graphics_are_adjusted(self):
        self._assume = a_project()\
            .with_main_file("A \\includegraphics[width=3cm]{img/foo} Z")\
            .with_image("img/foo.pdf")

        self._expect = a_project()\
            .with_merged_file(r"A \includegraphics[width=3cm]{img_foo} Z")\
            .with_image("img_foo.pdf")

        self._do_test_and_verify()

    def test_paths_with_extension(self):
        self._assume = a_project()\
            .with_main_file("A \\includegraphics[width=3cm]{img/foo.pdf} Z")\
            .with_image("img/foo.pdf")

        self._expect = a_project()\
            .with_merged_file(r"A \includegraphics[width=3cm]{img_foo} Z")\
            .with_image("img_foo.pdf")

        self._do_test_and_verify()

    def test_path_with_extension_in_a_different_case(self):
        self._assume = a_project()\
            .with_main_file("A \\includegraphics[width=3cm]{img/foo} Z")\
            .with_image("img/foo.PDF")

        self._expect = a_project()\
            .with_merged_file(r"A \includegraphics[width=3cm]{img_foo} Z")\
            .with_image("img_foo.PDF")

        self._do_test_and_verify()

    def test_path_to_local_images_are_not_adjusted(self):
        self._assume = a_project()\
            .with_main_file("A \\includegraphics[width=3cm]{foo} Z")\
            .with_image("foo.pdf")

        self._expect = a_project()\
            .with_merged_file(r"A \includegraphics[width=3cm]{foo} Z")\
            .with_image("foo.pdf")

        self._do_test_and_verify()

    def test_link_to_graphic_in_a_separate_file(self):
        self._assume = a_project()\
            .with_main_file("AAA \\input{slides/foo} BBB")\
            .with_file("slides/foo.tex", "\\includegraphics{foo}")\
            .with_image("foo.pdf")

        self._expect = a_project()\
            .with_merged_file("AAA \\includegraphics{foo} BBB")\
            .with_image("foo.pdf")

        self._do_test_and_verify()

    def test_multi_lines_directives(self):
        self._assume = a_project()\
            .with_main_file("\includegraphics[width=8cm]{%\n"
                            "img/foo%\n"
                            "}\n")\
            .with_image("img/foo.pdf")

        self._expect = a_project()\
            .with_merged_file("\\includegraphics[width=8cm]{img_foo}\n")\
            .with_image("img_foo.pdf")

        self._do_test_and_verify()

    def test_missing_graphics_are_detected(self):
        self._assume = a_project()\
            .with_main_file("\\includegraphics{foo}")

        with self.assertRaises(GraphicNotFound):
            self._do_test_and_verify()

    def test_includegraphics_are_reported(self):
        self._assume = a_project()\
            .with_main_file("\n\\includegraphics{foo}")\
            .with_image("foo.pdf")

        self._expect = a_project()\
            .with_merged_file("\n\\includegraphics{foo}")\
            .with_image("foo.pdf")

        self._do_test_and_verify()

        self._verify_ui_reports_fragment("main.tex", 2, "\\includegraphics{foo}")

    def test_local_paths(self):
        self._assume = a_project()\
            .with_main_file("A \\includegraphics{foo} Z")\
            .with_image("foo.pdf")

        self._expect = a_project()\
            .with_merged_file("A \\includegraphics{foo} Z")\
            .with_image("foo.pdf")

        self._runner._root_file = lambda name: Path.fromText("main.tex")

        self._do_test_and_verify()


class SVGIncludeTest(FlapTest):

    def testLinksToSVGAreAdjusted(self):
        self._assume = a_project()\
            .with_main_file("A \\includesvg{img/foo} Z")\
            .with_image("img/foo.svg")

        self._expect = a_project()\
            .with_merged_file("A \\includesvg{img_foo} Z")\
            .with_image("img_foo.svg")

        self._do_test_and_verify()

    def test_includesvg_in_separated_file(self):
        # TODO check if this example would actually compile in latex
        self._assume = a_project()\
            .with_main_file("A \\input{parts/foo} A")\
            .with_file("parts/foo.tex", "B \\includesvg{img/sources/test} B")\
            .with_image("img/sources/test.svg")

        self._expect = a_project()\
            .with_merged_file("A B \\includesvg{img_sources_test} B A")\
            .with_image("img_sources_test.svg")

        self._do_test_and_verify()

    def testSVGFilesAreCopiedEvenWhenJPGAreAvailable(self):
        self._assume = a_project()\
            .with_main_file("A \\includesvg{img/foo} Z")\
            .with_image("img/foo.eps")\
            .with_image("img/foo.svg")

        self._expect = a_project()\
            .with_merged_file(r"A \includesvg{img_foo} Z")\
            .with_image("img_foo.svg")

        self._do_test_and_verify()


class OverpicAdjuster(FlapTest):
    """
    Specification of the processor for 'overpic' environment
    """

    def test_overpic_environment_are_adjusted(self):
        self._assume = a_project()\
            .with_main_file("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{%\n"
                            "img/picture}\n"
                            "blablabla\n"
                            "\\end{overpic}\n")\
            .with_image("img/picture.pdf")

        self._expect = a_project()\
            .with_merged_file("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{img_picture}\n"
                              "blablabla\n"
                              "\\end{overpic}\n")\
            .with_image("img_picture.pdf")

        self._do_test_and_verify()


if __name__ == "__main__":
    main()


