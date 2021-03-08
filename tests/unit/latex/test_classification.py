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
        self._test((r"\foo", "", r"{blablabla}"),
                   r"\foo",
                   False)

    def test_macro_with_input(self):
        self._test((r"\foo", "#1", r"{\input{#1}}"),
                   r"\foo{my-file}",
                   True)

    def test_macro_with_include(self):
        self._test((r"\foo", "#1", r"{\include{#1}}"),
                   r"\foo{my-file}",
                   True)

    def test_macro_with_masked_input(self):
        self._test((r"\foo", "#1", r"{\def\input#1{blablab #1} \input{#1}}"),
                   r"\foo{my-file}",
                   False)

    def _test(self, macro, invocation, expected_category):
        self._define(*macro)
        self.assertEqual(expected_category,
                         self._classify(invocation))

    def _define(self, name, parameters, body):
        macro = self._macros.create(
            name,
            self._factory.as_list(parameters),
            self._factory.as_list(body))
        self._environment[name] = macro

    def _classify(self, expression):
        parser = Parser(self._factory.as_tokens(expression, "Unknown"),
                        self._factory,
                        self._environment)
        parser.evaluate()
        return parser.shall_expand()
