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

from flap.engine import Fragment
from flap.util.oofs import File, MissingFile
from flap.util.path import ROOT


class FragmentTest(TestCase):

    def setUp(self):
        self.file = File(None, ROOT / "main.tex", "xxx")
        self.fragment = Fragment(self.file, 13, "blah blah")

    def test_expose_line_number(self):
        self.assertEqual(self.fragment.line_number(), 13)

    def test_reject_negative_or_zero_line_number(self):
        with self.assertRaises(ValueError):
            Fragment(self.file, 0, "blah blah")

    def test_expose_file(self):
        self.assertEqual(self.fragment.file().fullname(), "main.tex")

    def test_reject_missing_file(self):
        with self.assertRaises(ValueError):
            Fragment(MissingFile(ROOT / "main.tex"), 13, "blah blah")

    def test_expose_fragment_text(self):
        self.assertEqual(self.fragment.text(), "blah blah")

    def test_detect_comments(self):
        self.assertFalse(self.fragment.is_commented_out())

    def test_should_be_sliceable(self):
        self.assertEqual(self.fragment[0:4].text(), "blah")


if __name__ == "__main__":
    main()
