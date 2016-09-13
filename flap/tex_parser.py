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


class Macro:

    def __init__(self, name):
        self._name = name
        self._parameters = []

    @property
    def name(self):
        return self._name

    def has_parameters(self):
        return len(self._parameters) > 0


class TokenStream:

    def __init__(self, input_stream):
        self._stream = iter(input_stream)

    def __iter__(self):
<<<<<<< HEAD
        return self
=======
       return self
>>>>>>> 236bad5c4d4572693dd2a0b71e9e01ef26556781

    def __next__(self):
        return Token(next(self._stream))

    def prepend(self, text):
        self._stream = chain(iter(text), self._stream)

<<<<<<< HEAD
    def extract_macro_name(self):
        return self._extract_while(lambda token: token.belongs_to_the_macro_name())

    def _extract_while(self, shall_include):
        buffer = ""
        for any_token in self:
            if shall_include(any_token):
                buffer += str(any_token)
            else:
                self.prepend([str(any_token)])
                return buffer
        return buffer

    def _extract_until(self, accept):
        return self._extract_while(lambda token: not accept(token))

    def extract_macro_parameters(self):
        parameters = [""]
        for any_token in self:
            if any_token.starts_replacement():
                self.prepend([str(any_token)])
                return parameters
            if any_token.starts_parameter():
                parameter = self._consume_parameter()
                parameters.append("#" + parameter)
                parameters.append("")
                continue
            parameters[-1] += str(any_token)
        return parameters

    def _consume_parameter(self):
        return self._extract_while(lambda token: token.belongs_to_parameter())

    def extract_replacement(self):
        assert next(self).starts_replacement()
        return self._extract_until(lambda token: token.ends_replacement())

=======
>>>>>>> 236bad5c4d4572693dd2a0b71e9e01ef26556781

class Token:

    def __init__(self, character):
        self._character = character

<<<<<<< HEAD
    def _is(self, character):
        return self._character == character

    def starts_a_macro(self):
        return self._is("\\")

    def belongs_to_the_macro_name(self):
        return self._character.isalpha()

    def starts_parameter(self):
        return self._is("#")

    def belongs_to_parameter(self):
        return self._character.isdigit()

    def starts_replacement(self):
        return self._is("{")

    def ends_replacement(self):
        return self._is("}")
=======
    def starts_a_macro(self):
        return self._character == "\\"

    def belongs_to_the_macro_name(self):
        return self.starts_a_macro() or self._character.isalpha()
>>>>>>> 236bad5c4d4572693dd2a0b71e9e01ef26556781

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
<<<<<<< HEAD
                (parameters, replacement) = self._match_macro(tokens)
                tokens.prepend(replacement)
            else:
                self._output.write(str(any_token))

    def _match_macro(self, tokens):
        name = tokens.extract_macro_name()
        if name == "def":
            self._define(tokens)
            return ([], "")
=======
                macro = self._match_macro(tokens)
                tokens.prepend(macro)
            else:
                self._output.write(str(any_token))

    def _match_macro(self, input_stream):
        name = self._read_macro_name_from(input_stream)
>>>>>>> 236bad5c4d4572693dd2a0b71e9e01ef26556781
        macro = self._environment.get(name, None)
        if macro is None:
            raise UnknownMacroException(name)
        return macro

<<<<<<< HEAD
    def _define(self, tokens):
        assert next(tokens).starts_a_macro()
        macro_name = tokens.extract_macro_name()
        parameters = tokens.extract_macro_parameters()
        replacement = tokens.extract_replacement()
        assert next(tokens).ends_replacement()
        self._environment[macro_name] = (parameters, replacement)
=======
    def _read_macro_name_from(self, input_stream):
        name = ""
        for any_token in input_stream:
            if any_token.belongs_to_the_macro_name():
                name += str(any_token)
        return name
>>>>>>> 236bad5c4d4572693dd2a0b71e9e01ef26556781


class UnknownMacroException(Exception):

    def __init__(self, macro_name):
        self._macro_name = macro_name
