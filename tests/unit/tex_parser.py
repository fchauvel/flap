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
from io import StringIO

from flap.tex_parser import TeXInterpreter, UnknownMacroException


class TeXParserTests(TestCase):

    def setUp(self):
        self.environment = dict()
        self.output = StringIO()
        self.tex = TeXInterpreter(self.environment, self.output)

    def test_typesetting_a_text(self):
        tex_input = "This is a text!"
        self.tex.evaluate(tex_input)

        self.assertEquals(tex_input, self.output.getvalue())

    def test_unknown_macro(self):
        with self.assertRaises(UnknownMacroException):
            self.tex.evaluate("\\name")

    def test_typesetting_a_macro(self):
        self.environment["name"] = "franck"
        self.tex.evaluate("\\name")
        self.assertEqual("franck", self.output.getvalue())


if __name__ == "__main__":
    main()