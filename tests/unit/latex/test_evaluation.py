#!/usr/bin/env python

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

from unittest import TestCase
from mock import MagicMock

from flap.latex.symbols import SymbolTable
from flap.latex.tokens import TokenFactory
from flap.latex.macros.factory import MacroFactory
from flap.latex.parser import Parser, Context, Factory


class ClassificationTests(TestCase):

    def setUp(self):
        self._engine = MagicMock()
        self._macros = MacroFactory(self._engine)
        self._symbols = SymbolTable.default()
        self._tokens = TokenFactory(self._symbols)
        self._factory = Factory(self._symbols)
        self._environment = Context(definitions=self._macros.all())

    def test_literal_macro(self):
        self._define(r"\foo", "", r"{blablabla}")
        self._verify_evaluation(r"\foo", "blablabla")

    def test_macro_that_uses_input(self):
        self._engine.content_of.return_value = "blabla"
        self._define(r"\foo", "#1", r"{File: \input{#1}}")
        self._verify_evaluation(r"\foo{my-file}", "File: blabla")

    def test_macro_that_redefines_input(self):
        self._define(r"\foo", "#1", r"{\def\input#1{File: #1}\input{#1}}")
        self._verify_evaluation(r"\foo{test.tex}", "File: test.tex")

    def test_macro_with_include(self):
        self._engine.content_of.return_value = "blabla"
        self._define(r"\foo", "#1", r"{\include{#1}}")
        self._verify_evaluation(r"\foo{my-file}", r"blabla\clearpage")

    def test_macro_with_masked_input(self):
        self._define(r"\foo", "#1", r"{\def\input#1{blabla #1}\input{#1}}")
        self._verify_evaluation(r"\foo{my-file}", "blabla my-file")

    def test_invoking_a_macro_with_a_group_as_argument(self):
        self._define(r"\foo", "(#1)", "{Text: #1}")
        self._verify_evaluation(r"\foo({bar!})", r"Text: bar!")

    def test_invoking_a_macro_with_two_parameters(self):
        self._define(r"\point", "(#1,#2)", "{X=#1 and Y=#2}")
        self._verify_evaluation(
            r"\point(12,{3 point 5})",
            "X=12 and Y=3 point 5")

    def test_macro_with_one_parameter(self):
        self._define(r"\foo", "#1", "{x=#1}")
        self._verify_evaluation(r"\foo{2}", r"x=2")

    def test_macro_with_parameter_scope(self):
        self._define(r"\foo", r"(#1,#2)", r"{\def\bar#1{Bar=#1}\bar#2 ; #1}")
        self._verify_evaluation(r"\foo(2,3)", r"Bar=3 ; 2")

    def test_defining_internal_macros(self):
        self._symbols.CHARACTER += "@"
        self._verify_evaluation(r"\def\internal@foo{\internal@bar}", "")
        self.assertEqual(self._macro(r"\internal@foo", "", r"{\internal@bar}"),
                         self._environment[r"\internal@foo"])

    def test_internal_macros(self):
        self._symbols.CHARACTER += "@"
        self._define(r"\internal@foo", "", r"{\internal@bar}")
        self._verify_evaluation(r"\internal@foo", "\\internal@bar")

    def _verify_evaluation(self, invocation, expected_category):
        self.assertEqual(expected_category,
                         self._evaluate(invocation))

    def _define(self, name, parameters, body):
        self._environment[name] = self._macro(name, parameters, body)

    def _macro(self, name, parameters, body):
        return self._macros.create(
            name,
            self._factory.as_list(parameters),
            self._factory.as_list(body))

    def _evaluate(self, expression):
        parser = Parser(self._factory.as_tokens(expression, "Unknown"),
                        self._factory,
                        self._environment)
        return "".join(map(str, parser.evaluate()))
