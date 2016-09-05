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

from unittest import TestCase, main, skip
from mock import MagicMock

from flap.FileSystem import InMemoryFileSystem, File, MissingFile
from flap.engine import Flap, Fragment, Listener, CommentsRemover, Processor, GraphicNotFound, TexFileNotFound
from flap.path import Path, ROOT, TEMP

from tests.commons import LatexProject, FlapTest


class FragmentTest(TestCase):
    """
    Specification of the Fragment class 
    """

    def setUp(self):
        self.file = File(None, ROOT / "main.tex", "xxx")
        self.fragment = Fragment(self.file, 13, "blah blah")

    def testShouldExposeLineNumber(self):
        self.assertEqual(self.fragment.line_number(), 13)

    def testShouldRejectNegativeOrZeroLineNumber(self):
        with self.assertRaises(ValueError):
            Fragment(self.file, 0, "blah blah")

    def testShouldExposeFile(self):
        self.assertEqual(self.fragment.file().fullname(), "main.tex")

    def testShouldRejectMissingFile(self):
        with self.assertRaises(ValueError):
            Fragment(MissingFile(ROOT / "main.tex"), 13, "blah blah")

    def testShouldExposeFragmentText(self):
        self.assertEqual(self.fragment.text(), "blah blah")

    def testShouldDetectComments(self):
        self.assertFalse(self.fragment.is_commented_out())

    def testShouldBeSliceable(self):
        self.assertEqual(self.fragment[0:4].text(), "blah")


class CommentRemoverTest(TestCase):

    def test_remove_commented_lines(self):
        self.runTest("\nfoo\n% this is a comment\nbar",
                     "\nfoo\nbar")

    def test_remove_end_line_comments(self):
        text = ("A"
                "\\includegraphics% This is a comment \n"
                "[width=8cm]{%\n"
                "foo%\n"
                "}\n"
                "B")
        expected = "A\\includegraphics[width=8cm]{foo}\nB"
        self.runTest(text, expected)

    def test_does_not_takes_percent_as_comments(self):
        input = ("25 \\% of that \n"
                 "% this is a comment \n"
                 "blah bla")
        expected_output = ("25 \\% of that \n"
                           "blah bla")
        self.runTest(input,
                     expected_output)

    def test_does_not_takes_verbatim_comments_as_comments(self):
        input = ("25 \\verb|%| of that \n"
                 "% this is a comment \n"
                 "blah bla")
        expected_output = ("25 \\verb|%| of that \n"
                           "blah bla")
        self.runTest(input,
                     expected_output)

    def runTest(self, text, expectation):
        source = File(None, TEMP / "test", None)
        source.isMissing = MagicMock()
        source.isMissing.return_value = False

        delegate = Processor()
        delegate.fragments = MagicMock()
        delegate.fragments.return_value = iter([Fragment(source, 1, text)])

        sut = CommentsRemover(delegate)

        result = list(sut.fragments())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text(), expectation)


class FlapUnitTest(FlapTest):
    """
    Provide some helper methods for create file in an in memory file system
    """

    def setUp(self):
        super().setUp()
        self.file_system = InMemoryFileSystem()
        self.listener = MagicMock(Listener())
        self.flap = Flap(self.file_system, self.listener)

    def run_flap(self, output=Flap.OUTPUT_FILE):
        super().run_flap(output)
        self.project.create_on(self.file_system)
        self.flap.flatten(self.project.root_latex_file, self.output_directory / self.merged_file)

    def verify_listener(self, handler, fileName, lineNumber, text):
        fragment = handler.call_args[0][0]
        self.assertEqual(fragment.file().fullname(), fileName)
        self.assertEqual(fragment.line_number(), lineNumber)
        self.assertEqual(fragment.text().strip(), text)


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


class InputMergerTests(FlapUnitTest):

    def test_simple_merge(self):
        self.project.root_latex_code = "blahblah \\input{foo} blah"
        self.project.parts["foo.tex"] = "bar"

        self.run_flap()

        self.verify_merge("blahblah bar blah")

    def test_simple_merge_with_extension(self):
        self.project.root_latex_code = "blahblah \\input{foo.tex} blah"
        self.project.parts["foo.tex"] = "bar"

        self.run_flap()

        self.verify_merge("blahblah bar blah")

    def test_subdirectory_merge(self):
        self.project.root_latex_code = "blahblah \\input{partA/foo} blah"
        self.project.parts["partA/foo.tex"] = "bar"

        self.run_flap()

        self.verify_merge("blahblah bar blah")

    def test_recursive_merge(self):
        self.project.root_latex_code = "A \\input{foo} Z"
        self.project.parts["foo.tex" ] = "B \\input{bar} Y"
        self.project.parts["bar.tex"] = "blah"

        self.run_flap()

        self.verify_merge("A B blah Y Z")

    def test_path_are_considered_from_root_in_recursive_input(self):
        self.project.root_latex_code = "A \\input{parts/foo} Z"
        self.project.parts["parts/foo.tex" ] = "B \\input{parts/subparts/bar} Y"
        self.project.parts["parts/subparts/bar.tex"] = "blah"

        self.run_flap()

        self.verify_merge("A B blah Y Z")

    def test_commented_lines_are_ignored(self):
        self.project.root_latex_code = "\n" \
                                       "blah blah blah\n" \
                                       "% \input{foo} \n" \
                                       "blah blah blah\n" \
                                       ""
        self.project.parts["foo.tex"] = "included content"

        self.run_flap()

        self.verify_merge("\n"
                           "blah blah blah\n"
                           "blah blah blah\n"
                           "")

    def test_multi_lines_path(self):
        self.project.root_latex_code = "A \\input{img/foo/%\n" \
                                       "bar/%\n" \
                                       "baz} B"
        self.project.parts["img/foo/bar/baz.tex"] = "xyz"

        self.run_flap()

        self.verify_merge("A xyz B")

    def test_input_directives_are_reported(self):
        self.project.root_latex_code = "blah blabh\n" \
                                       "\input{foo}"

        self.project.parts["foo.tex"] = "blah blah"

        self.run_flap()

        self.verify_listener(self.listener.on_input, "main.tex", 2, "\input{foo}")

    def test_missing_tex_file_are_detected(self):
        self.project.root_latex_code = "\n" \
                                       "\input{foo}"

        with self.assertRaises(TexFileNotFound):
            self.run_flap()


class IncludeMergeTest(FlapUnitTest):

    def test_simple_merge(self):
        self.project.root_latex_code = "blahblah \include{foo} blah"

        self.project.parts["foo.tex"] = "bar"

        self.run_flap()

        self.verify_merge("blahblah bar\clearpage  blah")

    def test_subdirectory_merge(self):
        self.project.root_latex_code = "blahblah \include{partA/foo} blah"

        self.project.parts["partA/foo.tex"] = "bar"

        self.run_flap()

        self.verify_merge("blahblah bar\clearpage  blah")

    def test_include_only_effect(self):
        self.project.root_latex_code = ("bla blab"
                                        "\includeonly{foo, baz}"
                                        "bla bla"
                                        "\include{foo}"
                                        "\include{bar}"
                                        "bla bla"
                                        "\include{baz}"
                                        "bla")

        self.project.parts["foo.tex"] = "foo"
        self.project.parts["bar.tex"] = "bar"
        self.project.parts["baz.tex"] = "baz"

        self.run_flap()

        self.verify_merge("bla blab"
                           "bla bla"
                           "foo\\clearpage "
                           "bla bla"
                           "baz\\clearpage "
                           "bla")

    def test_missing_tex_file_are_detected(self):
        self.project.root_latex_code = "\n" \
                                       "\\include{foo}"

        with self.assertRaises(TexFileNotFound):
            self.run_flap()


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

        self.verify_listener(self.listener.on_include_graphics, "main.tex", 2, "\\includegraphics{foo}")

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


if __name__ == "__main__":
    main()
