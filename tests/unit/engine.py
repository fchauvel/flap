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
from flap.engine import Flap, Fragment, Listener, CommentsRemover, Processor
from flap.path import Path, ROOT, TEMP


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
        self.project_directory = "project"
        self.main_tex_file = "main.tex"

    def _prepare_listener(self):
        self.listener = Listener()
        self.listener.on_flatten_complete = MagicMock()
        self.listener.on_input = MagicMock()
        self.listener.on_include_graphics = MagicMock()

    def verifyFile(self, path, content):
        result = self.fileSystem.open(path)
        self.assertTrue(result.exists(), "Missing file '%s'" % path)
        self.assertEqual(content, result.content(),  "Wrong merged")

    def create_file(self, location, content):
        path = Path.fromText(location)
        self.fileSystem.createFile(path, content)

    def create_main_file(self, content):
        self.create_file(self.project_directory + "/" + self.main_tex_file, content)

    def create_image(self, location):
        path = Path.fromText(self.project_directory + "/" + location)
        self.fileSystem.createFile(path, "image")

    def create_tex_file(self, location, content):
        self.create_file(self.project_directory + "/" + location, content)

    def open(self, location):
        return self.fileSystem.open(Path.fromText(self.project_directory + "/" + location))

    def run_flap(self):
        self.flap.flatten(ROOT / self.project_directory / self.main_tex_file, ROOT / "result")

    def verify_merged(self, content):
        self.verifyFile(ROOT / "result" / "merged.tex", content)

    def verify_image(self, path):
        self.verifyFile(ROOT / "result" / path, "image")

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
        self.create_main_file("aaa\n"
                              "\\endinput\n"
                              "ccc")
        self.run_flap()
        self.verify_merged("aaa\n")

    def test_endinput_in_a_separate_tex_file(self):
        self.create_main_file("aaa\n"
                              "\\input{foo}\n"
                              "ccc")
        self.create_tex_file("foo.tex", "bbb\n"
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
        self.create_main_file(r"blahblah \input{foo} blah")
        self.create_tex_file("foo.tex", "bar")

        self.run_flap()

        self.verify_merged("blahblah bar blah")

    def test_recursive_merge(self):
        self.create_main_file("A \input{foo} Z")
        self.create_tex_file("foo.tex", "B \input{bar} Y")
        self.create_tex_file("bar.tex", "blah")

        self.run_flap()

        self.verify_merged("A B blah Y Z")

    def test_commented_lines_are_ignored(self):
        self.create_main_file("\n"
                              "blah blah blah\n"
                              "% \input{foo} \n"
                              "blah blah blah\n"
                              "")
        self.create_tex_file("foo.tex", "included content")

        self.run_flap()

        self.verify_merged("\n"
                           "blah blah blah\n"
                           "\n"
                           "blah blah blah\n"
                           "")

    def test_multi_lines_path(self):
        self.create_main_file("""A \\input{img/foo/%
                   bar/%
                   baz} B""")
        self.create_tex_file("img/foo/bar/baz.tex", "xyz")

        self.run_flap()

        self.verify_merged("A xyz B")

    def test_input_directives_are_reported(self):
        self.create_main_file("""blah blabh
        \input{foo}""")
        self.create_tex_file("foo.tex", "blah blah")

        self.run_flap()

        self.verify_listener(self.listener.on_input, "main.tex", 2, "\input{foo}")


class IncludeMergeTest(FLaPTest):

    def test_simple_merge(self):
        self.create_main_file("blahblah \include{foo} blah")
        self.create_tex_file("foo.tex", "bar")

        self.run_flap()

        self.verify_merged("blahblah bar\clearpage  blah")

    def test_include_only_effect(self):
        self.create_main_file("bla blab"
                              "\includeonly{foo, baz}"
                              "bla bla"
                              "\include{foo}"
                              "\include{bar}"
                              "bla bla"
                              "\include{baz}"
                              "bla")
        self.create_tex_file("foo.tex", "foo")
        self.create_tex_file("bar.tex", "bar")
        self.create_tex_file("baz.tex", "baz")

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
        self.create_main_file("\\graphicspath{img/}"
                              "blabla"
                              "\\includegraphics[witdh=5cm]{plot}"
                              "blabla")
        self.create_image("img/plot.pdf")

        self.run_flap()

        self.verify_merged("blabla"
                           "\\includegraphics[witdh=5cm]{plot}"
                           "blabla")

class IncludeGraphicsProcessorTest(FLaPTest):
    """
    Tests the processing of \includegraphics directive
    """

    def test_links_to_graphics_are_adjusted(self):
        self.create_main_file(r"A \includegraphics[width=3cm]{img/foo} Z")
        self.create_image("img/foo.pdf")

        self.run_flap()

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_paths_with_extension(self):
        self.create_main_file(r"A \includegraphics[width=3cm]{img/foo.pdf} Z")
        self.create_image("img/foo.pdf")

        self.run_flap()

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_local_paths(self):
        self.create_main_file("A \\includegraphics[width=3cm]{foo} Z")
        self.create_image("foo.pdf")

        self.move_to_directory(self.project_directory)
        self.flap.flatten(Path.fromText("main.tex"), ROOT / "result")

        self.verify_merged(r"A \includegraphics[width=3cm]{foo} Z")
        self.verify_image("foo.pdf")

    def test_path_to_local_images_are_not_adjusted(self):
        self.create_main_file("\\includegraphics[interpolate,width=11.445cm]{%\n"
                              "startingPlace}")
        self.create_image("startingPlace.pdf")

        self.run_flap()

        self.verify_merged("\\includegraphics[interpolate,width=11.445cm]{startingPlace}")
        self.verify_image("startingPlace.pdf")

    def test_link_to_graphic_in_a_separate_file(self):
        self.create_main_file("aaa\n"
                              "\\input{slides/foo}\n"
                              "bbb")
        self.create_tex_file("slides/foo.tex", "ccc\n"
                                               "\\includegraphics{foo}\n"
                                               "ddd")
        self.create_image("foo.pdf")

        self.run_flap()

        self.verify_merged("aaa\n"
                           "ccc\n"
                           "\\includegraphics{foo}\n"
                           "ddd\n"
                           "bbb")
        self.verify_image("foo.pdf")

    def test_paths_are_recursively_adjusted(self):
        self.create_main_file(r"AA \input{foo} AA")
        self.create_tex_file("foo.tex", r"BB \includegraphics[width=3cm]{img/foo} BB")
        self.create_image("img/foo.pdf")

        self.run_flap()

        self.verify_merged(r"AA BB \includegraphics[width=3cm]{foo} BB AA")
        self.verify_image("foo.pdf")

    def test_multi_lines_directives(self):
        content = ("A"
                   "\includegraphics[width=8cm]{%\n"
                   "img/foo%\n"
                   "}\n"
                   "B")
        self.create_main_file(content)
        self.create_image("img/foo.pdf")

        self.run_flap()

        self.verify_merged("A\\includegraphics[width=8cm]{foo}\nB")
        self.verify_image("foo.pdf")

    def test_includegraphics_are_reported(self):
        self.create_main_file("""
        \includegraphics{foo}""")
        self.create_image("foo.pdf")

        self.run_flap()

        self.verify_listener(self.listener.on_include_graphics, "main.tex", 2, "\\includegraphics{foo}")


class SVGIncludeTest(FLaPTest):

    def testLinksToSVGAreAdjusted(self):
        self.create_main_file(r"A \includesvg{img/foo} Z")
        self.create_image("img/foo.svg")

        self.run_flap()

        self.verify_merged(r"A \includesvg{foo} Z")
        self.verify_image("foo.svg")

    def test_includesvg_in_separated_file(self):
        self.create_main_file("A \\input{parts/foo} A")
        self.create_tex_file("parts/foo.tex", "B \\includesvg{img/sources/test} B")
        self.create_image("img/sources/test.svg")

        self.run_flap()

        self.verify_merged("A B \\includesvg{test} B A")
        self.verify_image("test.svg")

    def testSVGFilesAreCopiedEvenWhenJPGAreAvailable(self):
        self.create_main_file(r"A \includesvg{img/foo} Z")

        images = ["img/foo.eps", "img/foo.svg"]
        for eachImage in images :
            self.create_image(eachImage)

        self.fileSystem.filesIn = MagicMock()
        self.fileSystem.filesIn.return_value = [ self.open(eachImage) for eachImage in images ]

        self.run_flap()

        self.verify_merged(r"A \includesvg{foo} Z")
        self.verify_image("foo.svg")


class OverpicAdjuster(FLaPTest):
    """
    Specification of the processor for 'overpic' environment
    """

    def test_overpic_environment_are_adjusted(self):
        self.create_main_file(r"""
        \begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{%
        img/picture}
        blablabla
        \end{overpic}
        """)
        self.create_image("img/picture.pdf")

        self.run_flap()

        self.verify_merged(r"""
        \begin{overpic}[scale=0.25,unit=1mm,grid,tics=10]{picture}
        blablabla
        \end{overpic}
        """)
        self.verify_image("picture.pdf")


class MiscellaneousTests(FLaPTest):

    def test_indentation_is_preserved(self):
        self.create_main_file("\t\\input{part}")
        self.create_tex_file("part.tex", "\n"
                                         "\\begin{center}\n"
                                         "\t\\includegraphics[width=4cm]{img/foo}\n"
                                         "  \\includegraphics[width=5cm]{img/foo}\n"
                                         "\\end{center}")
        self.create_image("img/foo.pdf")

        self.run_flap()

        self.verify_merged("\t\n"
                           "\\begin{center}\n"
                           "\t\\includegraphics[width=4cm]{foo}\n"
                           "  \\includegraphics[width=5cm]{foo}\n"
                           "\\end{center}")
        self.verify_image("foo.pdf")

    def test_missing_file_are_reported(self):
        self.create_main_file("blahblah \input{foo} blah")

        with self.assertRaises(ValueError):
            self.run_flap()

    def test_resources_are_copied(self):
        self.create_main_file("xxx")
        self.create_tex_file("style.cls", "whatever")

        self.run_flap()

        self.verifyFile(ROOT / "result" / "style.cls", "whatever")

    def test_reports_completion(self):
        self.create_main_file("xxx")

        self.run_flap()

        self.listener.on_flatten_complete.assert_called_once_with()

if __name__ == "__main__":
    main()
