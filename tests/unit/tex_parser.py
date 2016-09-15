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

from flap.tex_parser import TeXInterpreter, TokenStream, Macro, DefineMacro, UnknownMacroException, UnexpectedToken


class MacroTest(TestCase):

    def setUp(self):
        self.macro = Macro("foo", [], "bar")

    def test_macro_expose_their_name(self):
        self.assertEqual("foo", self.macro.name)


class TokenStreamTests(TestCase):

    def test_extract_until_find_word(self):
        tokens = TokenStream("abcde---bbb")
        actual = tokens._extract_until_pattern("---")
        self.assertEqual("abcde", actual)

    def test_extract_until_avoids_prefix(self):
        tokens = TokenStream("ab-cde---bbb")
        actual = tokens._extract_until_pattern("---")
        self.assertEqual("ab-cde", actual)

    def test_extract_until_detects_missing_patterns(self):
        tokens = TokenStream("abcde---bbb")
        with self.assertRaises(UnexpectedToken):
            actual = tokens._extract_until_pattern("zzzz")


class TeXParserTests(TestCase):

    def setUp(self):
        self.environment = dict()
        self._output = StringIO()
        self.tex = TeXInterpreter(self.environment, self._output)
        self.tex.define(DefineMacro())

    def output(self):
        return self._output.getvalue()

    def test_typesetting_a_text(self):
        tex_input = "This is a text!"
        self.tex.evaluate(tex_input)

        self.assertEquals(tex_input, self.output())

    def test_unknown_macro(self):
        with self.assertRaises(UnknownMacroException):
            self.tex.evaluate(r"\name")

    def test_typesetting_a_macro(self):
        self.tex.define(Macro("name", [""], "franck"))
        self.tex.evaluate(r"Hello \name")
        self.assertEqual("Hello franck", self.output())

    def test_definition_macro(self):
        self.tex.evaluate(r"\def\hello{Hi Guys!}")
        self.assertEqual(Macro("hello", [""], "Hi Guys!"), self.environment["hello"])

    def test_expanding_a_macro(self):
        self.tex.define(Macro("hello", [""], "Hi Guys!"))
        self.tex.evaluate(r"\hello")
        self.assertEqual("Hi Guys!", self.output())

    def test_defining_a_one_parameter_macro(self):
        self.tex.evaluate(r"\def\value(#1){The value is '#1'!}")
        self.assertEquals(Macro("value", ["(", "#1", ")"], "The value is '#1'!"), self.environment["value"])

    def test_expanding_a_one_parameter_macro(self):
        self.tex.define(Macro("value", ["(", "#1", ")"], "The value is '#1'!"))
        self.tex.evaluate(r"\value(123)")
        self.assertEqual("The value is '123'!", self.output())

    def test_expanding_a_one_parameter_macro_with_a_different_syntax(self):
        self.tex.define(Macro("value", ["[", "#1", "]"], "The value is '#1'!"))
        self.tex.evaluate(r"\value[123]")
        self.assertEqual("The value is '123'!", self.output())

    def test_expanding_a_two_parameters_macro(self):
        self.tex.define(Macro("values", ["#1", "---", "#2"], "The values are '#1' and '#2'!"))
        self.tex.evaluate(r"\values123---234")
        self.assertEqual("The values are '123' and '234'!", self.output())

    def test_expanding_a_three_parameters_macro(self):
        self.tex.define(Macro("values",  ["#1", ":", "#2", ">", "#3"], "The values are '#1', '#2' and '#3'!"))
        self.tex.evaluate(r"\values23:45>32")
        self.assertEqual("The values are '23', '45' and '32'!", self.output())

    def test_typesetting_a_comment(self):
        self.tex.evaluate(r"Some text % A comment!")
        self.assertEqual("Some text % A comment!", self.output())

    def test_commented_macro_are_ignored(self):
        self.tex.define(Macro("foo", [""], "bar!"))
        self.tex.evaluate(r"blahblah blah % \foo")
        self.assertEqual(r"blahblah blah % \foo", self.output())

    def test_comments_only_until_the_end_of_the_line(self):
        self.tex.define(Macro("foo", [""], "bar!"))
        self.tex.evaluate("blahblah blah % \\foo \n\\foo")
        self.assertEqual("blahblah blah % \\foo \nbar!", self.output())


if __name__ == "__main__":
    main()