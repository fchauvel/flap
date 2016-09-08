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
from mock import MagicMock
from tests.unit.engine import FlapUnitTest
from flap.engine import GraphicNotFound


class GraphicPathTest(FlapUnitTest):
    """
    Specification of the graphic path processing
    """

    def test_graphic_are_adjusted_accordingly(self):
        self.project.root_latex_code = "\\graphicspath{img/}" \
                                        "blabla" \
                                        "\\includegraphics[witdh=5cm]{plot}" \
                                        "blabla"

        self.project.images = ["img/plot.pdf"]

        self.run_flap()

        self.verify_merge("blabla"
                           "\\includegraphics[witdh=5cm]{img_plot}"
                           "blabla")

    def test_escaped_graphicpath(self):
        self.project.root_latex_code = "\\graphicspath{{./img/}}" \
                                        "blabla" \
                                        "\\includegraphics[witdh=5cm]{plot}" \
                                        "blabla"

        self.project.images = ["img/plot.pdf"]

        self.run_flap()

        self.verify_merge("blabla"
                           "\\includegraphics[witdh=5cm]{img_plot}"
                           "blabla")


class IncludeGraphicsProcessorTest(FlapUnitTest):
    """
    Tests the processing of \includegraphics directive
    """

    def test_links_to_graphics_are_adjusted(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{img/foo} Z"

        self.project.images = ["img/foo.pdf"]

        self.run_flap()

        self.verify_merge(r"A \includegraphics[width=3cm]{img_foo} Z")
        self.verify_image("img_foo.pdf")

    def test_paths_with_extension(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{img/foo.pdf} Z"

        self.project.images = ["img/foo.pdf"]

        self.run_flap()

        self.verify_merge(r"A \includegraphics[width=3cm]{img_foo} Z")
        self.verify_image("img_foo.pdf")

    def test_path_with_extension_in_a_different_case(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{img/foo} Z"

        self.project.images = ["img/foo.PDF"]

        self.run_flap()

        self.verify_merge(r"A \includegraphics[width=3cm]{img_foo} Z")
        self.verify_image("img_foo.PDF")

    def test_local_paths(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{foo} Z"

        self.project.images_directory = None
        self.project.images = ["foo.pdf"]

        self.project.create_on(self.file_system)

        self.file_system.move_to_directory(self.project.directory)
        self.flap.flatten(self.project.root_latex_file, self.output_directory)

        self.verify_merge(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_path_to_local_images_are_not_adjusted(self):
        self.project.root_latex_code = ("\\includegraphics[interpolate,width=11.445cm]{%\n"
                                        "startingPlace}")

        self.project.images_directory = None
        self.project.images = ["startingPlace.pdf"]

        self.run_flap()

        self.verify_merge("\\includegraphics[interpolate,width=11.445cm]{startingPlace}")
        self.verify_image("startingPlace.pdf")

    def test_link_to_graphic_in_a_separate_file(self):
        self.project.root_latex_code = ("aaa\n"
                                        "\\input{slides/foo}\n"
                                        "bbb")
        self.project.parts["slides/foo.tex"] = ("ccc\n"
                                                "\\includegraphics{foo}\n"
                                                "ddd")
        self.project.images_directory = None
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merge("aaa\n"
                           "ccc\n"
                           "\\includegraphics{foo}\n"
                           "ddd\n"
                           "bbb")
        self.verify_image("foo.pdf")

    def test_paths_are_recursively_adjusted(self):
        self.project.root_latex_code = "AA \\input{foo} AA"
        self.project.parts["foo.tex"] = "BB \\includegraphics[width=3cm]{img/foo} BB"

        self.project.images = ["img/foo.pdf"]

        self.run_flap()

        self.verify_merge(r"AA BB \includegraphics[width=3cm]{img_foo} BB AA")
        self.verify_image("img_foo.pdf")

    def test_multi_lines_directives(self):
        self.project.root_latex_code = ("A"
                                        "\includegraphics[width=8cm]{%\n"
                                        "img/foo%\n"
                                        "}\n"
                                        "B")
        self.project.images = ["img/foo.pdf"]

        self.run_flap()

        self.verify_merge("A\\includegraphics[width=8cm]{img_foo}\nB")
        self.verify_image("img_foo.pdf")

    def test_includegraphics_are_reported(self):
        self.project.root_latex_code = ("\n"
                                        "\\includegraphics{foo}")

        self.project.images_directory = None
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_listener(self.listener.on_fragment, "main.tex", 2, "\\includegraphics{foo}")

    def test_missing_graphics_are_detected(self):
        self.project.root_latex_code = "\\includegraphics{foo}"

        with self.assertRaises(GraphicNotFound):
            self.run_flap()

class SVGIncludeTest(FlapUnitTest):

    def testLinksToSVGAreAdjusted(self):
        self.project.root_latex_code = "A \\includesvg{img/foo} Z"

        self.project.images = ["img/foo.svg"]

        self.run_flap()

        self.verify_merge(r"A \includesvg{img_foo} Z")
        self.verify_image("img_foo.svg")

    def test_includesvg_in_separated_file(self):
        # TODO check if this example would actually compile in latex
        self.project.root_latex_code =  "A \\input{parts/foo} A"
        self.project.parts["parts/foo.tex"] = "B \\includesvg{img/sources/test} B"

        self.project.images = ["img/sources/test.svg"]

        self.run_flap()

        self.verify_merge("A B \\includesvg{img_sources_test} B A")
        self.verify_image("img_sources_test.svg")

    def testSVGFilesAreCopiedEvenWhenJPGAreAvailable(self):
        self.project.root_latex_code =  "A \\includesvg{img/foo} Z"

        self.project.images = ["img/foo.eps", "img/foo.svg"]

        self.project.create_on(self.file_system)

        self.file_system.filesIn = MagicMock()
        self.file_system.filesIn.return_value = [ self.file_system.open(self.project.directory / eachImage) for eachImage in self.project.images ]

        self.run_flap()

        self.verify_merge(r"A \includesvg{img_foo} Z")
        self.verify_image("img_foo.svg")


class OverpicAdjuster(FlapUnitTest):
    """
    Specification of the processor for 'overpic' environment
    """

    def test_overpic_environment_are_adjusted(self):
        self.project.root_latex_code = ("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{%\n"
                                        "img/picture}\n"
                                        "blablabla\n"
                                        "\\end{overpic}\n"
                                        "")
        self.project.images = ["img/picture.pdf"]

        self.run_flap()

        self.verify_merge("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{img_picture}\n"
                           "blablabla\n"
                           "\\end{overpic}\n"
                           "")
        self.verify_image("img_picture.pdf")


if __name__ == "__main__":
    main()


