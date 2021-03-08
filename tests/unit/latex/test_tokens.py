#!/usr/bin/env python

#
# Copyright (C) 2015-2016 The FLaP authors
# This file is part of FLaP.
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

from flap.latex.commons import Position
from flap.latex.tokens import SymbolTable, Token, TokenFactory


class TokenTests(TestCase):

    def setUp(self):
        self._tokens = TokenFactory(SymbolTable.default())
        self._token = self._tokens.character(Position(1, 1), "a")

    def test_equals_itself(self):
        self.assertEqual(self._token, self._token)

    def test_equals_a_similar_tokens(self):
        self.assertEqual(
            self._tokens.character(
                Position(
                    1,
                    1),
                "a"),
            self._token)

    def test_differs_from_a_different_character(self):
        self.assertNotEqual(
            self._tokens.character(
                Position(
                    1,
                    1),
                "b"),
            self._token)

    def test_differs_from_an_object_of_another_type(self):
        self.assertNotEqual("foo", self._token)

    def test_print_properly(self):
        self.assertEqual(
            Token.DISPLAY.format(
                text="a", category="character", location=Position(
                    1, 1)), repr(
                self._token))


if __name__ == '__main__':
    main()
