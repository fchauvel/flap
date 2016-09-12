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

from itertools import chain


class TokenStream:

    def __init__(self, input_stream):
        self._stream = iter(input_stream)

    def __iter__(self):
       return self

    def __next__(self):
        return Token(next(self._stream))

    def prepend(self, text):
        self._stream = chain(iter(text), self._stream)


class Token:

    def __init__(self, character):
        self._character = character

    def starts_a_macro(self):
        return self._character == "\\"

    def belongs_to_the_macro_name(self):
        return self.starts_a_macro() or self._character.isalpha()

    def __str__(self):
        return self._character


class TeXInterpreter:
    """
    Parse a TeX program
    """

    def __init__(self, environment, output):
        self._environment = environment
        self._output = output

    def evaluate(self, input):
        tokens = TokenStream(input)
        for any_token in tokens:
            if any_token.starts_a_macro():
                macro = self._match_macro(tokens)
                tokens.prepend(macro)
            else:
                self._output.write(str(any_token))

    def _match_macro(self, input_stream):
        name = self._read_macro_name_from(input_stream)
        macro = self._environment.get(name, None)
        if macro is None:
            raise UnknownMacroException(name)
        return macro

    def _read_macro_name_from(self, input_stream):
        name = ""
        for any_token in input_stream:
            if any_token.belongs_to_the_macro_name():
                name += str(any_token)
        return name


class UnknownMacroException(Exception):

    def __init__(self, macro_name):
        self._macro_name = macro_name
