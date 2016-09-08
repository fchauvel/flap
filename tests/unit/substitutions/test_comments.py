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

from unittest import TestCase, main
from mock import MagicMock

from flap.engine import Fragment, Processor
from flap.substitutions.comments import CommentsRemover
from flap.path import TEMP
from flap.FileSystem import File


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


if __name__ == "__main__":
    main()