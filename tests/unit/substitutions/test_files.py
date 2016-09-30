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

from flap.engine import TexFileNotFound
from tests.commons import FlapTest, a_project


class InputMergerTests(FlapTest):

    def test_simple_merge(self):
        self._assume = a_project()\
            .with_main_file("blahblah \\input{foo} blah")\
            .with_file("foo.tex", "bar")

        self._expect = a_project()\
            .with_merged_file("blahblah bar blah")

        self._do_test_and_verify()

    def test_simple_merge_with_extension(self):
        self._assume = a_project()\
            .with_main_file("blahblah \\input{foo.tex} blah")\
            .with_file("foo.tex", "bar")

        self._expect = a_project()\
            .with_merged_file("blahblah bar blah")

        self._do_test_and_verify()

    def test_subdirectory_merge(self):
        self._assume = a_project()\
            .with_main_file("blahblah \\input{partA/foo} blah")\
            .with_file("partA/foo.tex", "bar")

        self._expect = a_project()\
            .with_merged_file("blahblah bar blah")

        self._do_test_and_verify()

    def test_recursive_merge(self):
        self._assume = a_project()\
            .with_main_file("A \\input{foo} Z")\
            .with_file("foo.tex", "B \\input{bar} Y")\
            .with_file("bar.tex", "blah")

        self._expect = a_project()\
            .with_merged_file("A B blah Y Z")

        self._do_test_and_verify()

    def test_path_are_considered_from_root_in_recursive_input(self):
        self._assume = a_project()\
            .with_main_file("A \\input{parts/foo} Z")\
            .with_file("parts/foo.tex", "B \\input{parts/subparts/bar} Y")\
            .with_file("parts/subparts/bar.tex", "blah")

        self._expect = a_project()\
            .with_merged_file("A B blah Y Z")

        self._do_test_and_verify()

    def test_commented_inputs_are_ignored(self):
        self._assume = a_project()\
            .with_main_file("blah blah blah\n"
                            "% \input{foo} \n"
                            "blah blah blah\n")\
            .with_file("foo.tex", "included content")

        self._expect = a_project()\
            .with_merged_file("blah blah blah\n"
                              "blah blah blah\n")

        self._do_test_and_verify()

    def test_multi_lines_path(self):
        self._assume = a_project()\
            .with_main_file("A \\input{parts/foo/%\n"
                            "bar/%\n"
                            "baz} B")\
            .with_file("parts/foo/bar/baz.tex", "xyz")

        self._expect = a_project()\
            .with_merged_file("A xyz B")

        self._do_test_and_verify()

    def test_input_directives_are_reported(self):
        self._assume = a_project()\
            .with_main_file("first line\n"
                            "\input{foo}")\
            .with_file("foo.tex", "second line")

        self._expect = a_project()\
            .with_merged_file("first line\n"
                              "second line")

        self._do_test_and_verify()
        self._verify_ui_reports_fragment("main.tex", 2, "\input{foo}")

    def test_missing_tex_file_are_detected(self):
        self._assume = a_project()\
            .with_main_file("\input{foo}")

        with self.assertRaises(TexFileNotFound):
            self._do_test_and_verify()


class SubfileMergerTests(FlapTest):

    def test_simple_merge(self):
        self._assume = a_project()\
            .with_main_file("\\subfile{foo}")\
            .with_file("foo.tex", "\\documentclass[../main.tex]{subfiles}" \
                                  "\\begin{document}" \
                                  "Blahblah blah!\\n" \
                                  "\\end{document}")

        self._expect = a_project()\
            .with_merged_file("Blahblah blah!\\n")

        self._do_test_and_verify()

    def test_recursive_merge(self):
        self._assume = a_project()\
            .with_main_file("PRE\\subfile{subpart}POST")\
            .with_file("subpart.tex", "\\documentclass[../main.tex]{subfiles}" \
                                      "\\begin{document}\\n" \
                                      "PRE\\subfile{subsubpart}POST\\n" \
                                      "\\end{document}")\
            .with_file("subsubpart.tex", "\\documentclass[../main.tex]{subfiles}" \
                                         "\\begin{document}\\n" \
                                         "Blahblah blah!\\n" \
                                         "\\end{document}")

        self._expect = a_project()\
            .with_merged_file("PRE\\n"
                              "PRE\\n"
                              "Blahblah blah!\\n"
                              "POST\\n"
                              "POST")

        self._do_test_and_verify()

    def test_does_not_break_document(self):
        self._assume = a_project()\
            .with_main_file("\\documentclass{article}\n"
                            "\\usepackage{graphicx}\n"
                            "\\begin{document}\n"
                            "This is my document\n"
                            "\\end{document}\n")

        self._expect = a_project()\
            .with_merged_file("\\documentclass{article}\n"
                              "\\usepackage{graphicx}\n"
                              "\\begin{document}\n"
                              "This is my document\n"
                              "\\end{document}\n")

        self._do_test_and_verify()


class IncludeMergeTest(FlapTest):

    def test_simple_merge(self):
        self._assume = a_project()\
            .with_main_file("blahblah \include{foo} blah")\
            .with_file("foo.tex", "bar")

        self._expect = a_project()\
            .with_merged_file("blahblah bar\clearpage  blah")

        self._do_test_and_verify()

    def test_subdirectory_merge(self):
        self._assume = a_project()\
            .with_main_file("blahblah \include{partA/foo} blah")\
            .with_file("partA/foo.tex", "bar")

        self._expect = a_project()\
            .with_merged_file("blahblah bar\clearpage  blah")

        self._do_test_and_verify()

    def test_include_only_effect(self):
        self._assume = a_project()\
            .with_main_file("bla blab"
                            "\includeonly{foo, baz}"
                            "bla bla"
                            "\include{foo}"
                            "\include{bar}"
                            "bla bla"
                            "\include{baz}"
                            "bla")\
            .with_file("foo.tex", "foo")\
            .with_file("bar.tex", "bar")\
            .with_file("baz.tex", "baz")

        self._expect = a_project()\
            .with_merged_file("bla blab"
                              "bla bla"
                              "foo\\clearpage "
                              "bla bla"
                              "baz\\clearpage "
                              "bla")

        self._do_test_and_verify()

    def test_missing_tex_file_are_detected(self):
        self._assume = a_project()\
            .with_main_file("\include{foo}")

        with self.assertRaises(TexFileNotFound):
            self._do_test_and_verify()
