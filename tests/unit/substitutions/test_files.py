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

from flap.engine import TexFileNotFound


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

        self.verify_listener(self.listener.on_fragment, "main.tex", 2, "\input{foo}")

    def test_missing_tex_file_are_detected(self):
        self.project.root_latex_code = "\n" \
                                       "\input{foo}"

        with self.assertRaises(TexFileNotFound):
            self.run_flap()


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
        self.project.root_latex_code = "PRE\\subfile{subpart}POST"

        self.project.parts["subpart.tex"] \
            = "\\documentclass[../main.tex]{subfiles}" \
              "\\begin{document}\\n" \
              "PRE\\subfile{subsubpart}POST\\n" \
              "\\end{document}"

        self.project.parts["subsubpart.tex"] \
            = "\\documentclass[../main.tex]{subfiles}" \
              "\\begin{document}\\n" \
              "Blahblah blah!\\n" \
              "\\end{document}"

        self.run_flap()

        self.verify_merge("PRE\\n"
                          "PRE\\n"
                          "Blahblah blah!\\n"
                          "POST\\n"
                          "POST")

    def test_does_not_break_document(self):
        self.project.root_latex_code = \
            "\\documentclass{article}\n" \
            "\\usepackage{graphicx}\n" \
            "\\begin{document}\n" \
            "This is my document\n" \
            "\\end{document}\n"

        self.run_flap()

        self.verify_merge(self.project.root_latex_code)


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
