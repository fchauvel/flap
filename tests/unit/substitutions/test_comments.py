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
from tests.commons import FlapTest, a_project


class CommentRemoverTest(FlapTest):

    def test_remove_commented_lines(self):
        self._assume = a_project()\
            .with_main_file("\nfoo\n"
                            "% this is a comment\n"
                            "bar")

        self._expect = a_project()\
            .with_merged_file("\nfoo\nbar")

        self._do_test_and_verify()

    def test_remove_end_line_comments(self):
        self._assume = a_project()\
            .with_main_file("A"
                            "\\includegraphics% This is a comment \n"
                            "[width=8cm]{%\n"
                            "foo%\n"
                            "}\n"
                            "B")\
            .with_image("foo.pdf")

        self._expect = a_project()\
            .with_merged_file("A\\includegraphics[width=8cm]{foo}\n"
                              "B")\
            .with_image("foo.pdf")

        self._do_test_and_verify()

    def test_does_not_takes_percent_as_comments(self):
        self._assume = a_project()\
            .with_main_file("25 \\% of that \n"
                            "% this is a comment \n"
                            "blah bla")

        self._expect = a_project()\
            .with_merged_file("25 \\% of that \n"
                              "blah bla")

        self._do_test_and_verify()

    def test_does_not_takes_verbatim_comments_as_comments(self):
        self._assume = a_project()\
            .with_main_file("25 \\verb|%| of that \n"
                            "% this is a comment \n"
                            "blah bla")

        self._expect = a_project()\
            .with_merged_file("25 \\verb|%| of that \n"
                              "blah bla")

        self._do_test_and_verify()


if __name__ == "__main__":
    main()