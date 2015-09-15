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

from tests.commons import LatexProject


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
    def testRemoveCommentedLines(self):
        self.runTest("\nfoo\n% this is a comment\nbar",
                     "\nfoo\n\nbar")

    def testRemoveEndLineComments(self):
        text = ("A"
                "\\includegraphics[width=8cm]{%\n"
                "foo%\n"
                "}\n"
                "B")
        self.runTest(text, "A\\includegraphics[width=8cm]{\nfoo\n}\nB")

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


class FLaPTest(TestCase):
    """
    Provide some helper methods for create file in an in memory file system
    """

    def setUp(self):
        self.fileSystem = InMemoryFileSystem()
        self._prepare_listener()
        self.flap = Flap(self.fileSystem, self.listener)
        self.project = LatexProject()

    def _prepare_listener(self):
        self.listener = MagicMock(Listener())

    def verifyFile(self, path, expected_content):
        actual_content = self.fileSystem.open(path)
        self.assertTrue(actual_content.exists(), "Missing file '%s'" % path)
        self.assertEqual(expected_content, actual_content.content(),  "Wrong merged")

    def create_file(self, location, content):
        path = Path.fromText(location)
        self.fileSystem.createFile(path, content)

    def open(self, location):
        return self.fileSystem.open(Path.fromText(self.project_directory + "/" + location))

    def run_flap(self):
        self.project.create_on(self.fileSystem)
        self.flap.flatten(self.project.root_latex_file, ROOT / "result")

    def verify_merged(self, content):
        self.verifyFile(ROOT / "result" / "merged.tex", content)

    def verify_image(self, path):
        self.verifyFile(ROOT / "result" / path, LatexProject.IMAGE_CONTENT)

    def verify_listener(self, handler, fileName, lineNumber, text):
        fragment = handler.call_args[0][0]
        self.assertEqual(fragment.file().fullname(), fileName)
        self.assertEqual(fragment.line_number(), lineNumber)
        self.assertEqual(fragment.text().strip(), text)

    def move_to_directory(self, directory):
        self.fileSystem.move_to_directory(Path.fromText(directory))


class TestEndinputRemover(FLaPTest):
    """
    Specify the behaviour of the Endinput remover
    """

    def test_endinput_mask_subsequent_content(self):
        self.project.root_latex_code = "aaa\n" \
                                       "\\endinput\n" \
                                       "ccc"
        self.run_flap()
        self.verify_merged("aaa\n")

    def test_endinput_in_a_separate_tex_file(self):
        self.project.root_latex_code = "aaa\n" \
                                       "\\input{foo}\n" \
                                       "ccc"

        self.project.parts["foo.tex"] = ("bbb\n"
                                         "bbb\n"
                                         "\\endinput\n"
                                         "zzz")
        self.run_flap()
        self.verify_merged("aaa\n"
                           "bbb\n"
                           "bbb\n\n"
                           "ccc")


class InputMergerTests(FLaPTest):

    def test_simple_merge(self):
        self.project.root_latex_code = "blahblah \\input{foo} blah"
        self.project.parts["foo.tex"] = "bar"

        self.run_flap()

        self.verify_merged("blahblah bar blah")

    def test_recursive_merge(self):
        self.project.root_latex_code = "A \input{foo} Z"
        self.project.parts["foo.tex" ] = "B \input{bar} Y"
        self.project.parts["bar.tex"] = "blah"

        self.run_flap()

        self.verify_merged("A B blah Y Z")

    def test_commented_lines_are_ignored(self):
        self.project.root_latex_code = "\n" \
                                       "blah blah blah\n" \
                                       "% \input{foo} \n" \
                                       "blah blah blah\n" \
                                       ""
        self.project.parts["foo.tex"] = "included content"

        self.run_flap()

        self.verify_merged("\n"
                           "blah blah blah\n"
                           "\n"
                           "blah blah blah\n"
                           "")

    def test_multi_lines_path(self):
        self.project.root_latex_code = "A \\input{img/foo/%\n" \
                                       "bar/%\n" \
                                       "baz} B"
        self.project.parts["img/foo/bar/baz.tex"] = "xyz"

        self.run_flap()

        self.verify_merged("A xyz B")

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


class IncludeMergeTest(FLaPTest):

    def test_simple_merge(self):
        self.project.root_latex_code = "blahblah \include{foo} blah"

        self.project.parts["foo.tex"] = "bar"

        self.run_flap()

        self.verify_merged("blahblah bar\clearpage  blah")

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

        self.verify_merged("bla blab"
                           "bla bla"
                           "foo\\clearpage "
                           "bla bla"
                           "baz\\clearpage "
                           "bla")


class GraphicPathTest(FLaPTest):
    """
    Specification of the graphic path processing
    """

    def test_graphic_are_adjusted_accordingly(self):
        self.project.root_latex_code = "\\graphicspath{img/}" \
                                        "blabla" \
                                        "\\includegraphics[witdh=5cm]{plot}" \
                                        "blabla"

        self.project.images_directory = "img"
        self.project.images = ["plot.pdf"]

        self.run_flap()

        self.verify_merged("blabla"
                           "\\includegraphics[witdh=5cm]{plot}"
                           "blabla")


class IncludeGraphicsProcessorTest(FLaPTest):
    """
    Tests the processing of \includegraphics directive
    """

    def test_links_to_graphics_are_adjusted(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{img/foo} Z"

        self.project.images_directory = "img"
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_paths_with_extension(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{img/foo.pdf} Z"

        self.project.images_directory = "img"
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_local_paths(self):
        self.project.root_latex_code = "A \\includegraphics[width=3cm]{foo} Z"

        self.project.images_directory = None
        self.project.images = ["foo.pdf"]

        self.project.create_on(self.fileSystem)

        self.fileSystem.move_to_directory(self.project.directory)
        self.flap.flatten(self.project.root_latex_file, ROOT / "result")

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_path_to_local_images_are_not_adjusted(self):
        self.project.root_latex_code = ("\\includegraphics[interpolate,width=11.445cm]{%\n"
                                        "startingPlace}")

        self.project.images_directory = None
        self.project.images = ["startingPlace.pdf"]

        self.run_flap()

        self.verify_merged("\\includegraphics[interpolate,width=11.445cm]{startingPlace}")
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

        self.verify_merged("aaa\n"
                           "ccc\n"
                           "\\includegraphics{foo}\n"
                           "ddd\n"
                           "bbb")
        self.verify_image("foo.pdf")

    def test_paths_are_recursively_adjusted(self):
        self.project.root_latex_code = "AA \\input{foo} AA"
        self.project.parts["foo.tex"] = "BB \\includegraphics[width=3cm]{img/foo} BB"

        self.project.images_directory = "img"
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merged(r"AA BB \includegraphics[width=3cm]{foo} BB AA")
        self.verify_image("foo.pdf")

    def test_multi_lines_directives(self):
        self.project.root_latex_code = ("A"
                                        "\includegraphics[width=8cm]{%\n"
                                        "img/foo%\n"
                                        "}\n"
                                        "B")
        self.project.images_directory = "img"
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merged("A\\includegraphics[width=8cm]{foo}\nB")
        self.verify_image("foo.pdf")

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




class SVGIncludeTest(FLaPTest):

    def testLinksToSVGAreAdjusted(self):
        self.project.root_latex_code = "A \\includesvg{img/foo} Z"

        self.project.images_directory = "img"
        self.project.images = ["foo.svg"]

        self.run_flap()

        self.verify_merged(r"A \includesvg{foo} Z")
        self.verify_image("foo.svg")

    def test_includesvg_in_separated_file(self):
        self.project.root_latex_code =  "A \\input{parts/foo} A"
        self.project.parts["parts/foo.tex"] = "B \\includesvg{img/sources/test} B"

        self.project.images_directory = "img/sources"
        self.project.images = ["test.svg"]

        self.run_flap()

        self.verify_merged("A B \\includesvg{test} B A")
        self.verify_image("test.svg")

    def testSVGFilesAreCopiedEvenWhenJPGAreAvailable(self):
        self.project.root_latex_code =  "A \\includesvg{img/foo} Z"

        self.project.images_directory = "img"
        self.project.images = ["foo.eps", "foo.svg"]

        self.project.create_on(self.fileSystem)

        self.fileSystem.filesIn = MagicMock()
        self.fileSystem.filesIn.return_value = [ self.fileSystem.open(self.project.path_to_image(eachImage)) for eachImage in self.project.images ]

        self.run_flap()

        self.verify_merged(r"A \includesvg{foo} Z")
        self.verify_image("foo.svg")


class OverpicAdjuster(FLaPTest):
    """
    Specification of the processor for 'overpic' environment
    """

    def test_overpic_environment_are_adjusted(self):
        self.project.root_latex_code = ("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{%\n"
                                        "img/picture}\n"
                                        "blablabla\n"
                                        "\\end{overpic}\n"
                                        "")
        self.project.images_directory = "img"
        self.project.images = ["picture.pdf"]

        self.run_flap()

        self.verify_merged("\\begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{picture}\n"
                           "blablabla\n"
                           "\\end{overpic}\n"
                           "")
        self.verify_image("picture.pdf")


class MiscellaneousTests(FLaPTest):

    def test_indentation_is_preserved(self):
        self.project.root_latex_code = "\t\\input{part}"
        self.project.parts["part.tex"] = ("\n"
                                          "\\begin{center}\n"
                                          "\t\\includegraphics[width=4cm]{img/foo}\n"
                                          "  \\includegraphics[width=5cm]{img/foo}\n"
                                          "\\end{center}")
        self.project.images_directory = "img"
        self.project.images = ["foo.pdf"]

        self.run_flap()

        self.verify_merged("\t\n"
                           "\\begin{center}\n"
                           "\t\\includegraphics[width=4cm]{foo}\n"
                           "  \\includegraphics[width=5cm]{foo}\n"
                           "\\end{center}")
        self.verify_image("foo.pdf")

    def test_resources_are_copied(self):
        self.project.root_latex_code = "xxx"
        self.project.parts["style.cls"] = "whatever"

        self.run_flap()

        self.verifyFile(ROOT / "result" / "style.cls", "whatever")


if __name__ == "__main__":
    main()
