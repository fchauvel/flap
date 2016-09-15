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

from re import sub
from itertools import chain


class Macro:

    def __init__(self, name, parameters, replacement):
        self._name = name
        self._parameters = parameters
        self._replacement = replacement

    @property
    def name(self):
        return self._name

    def evaluate(self, interpreter, tokens):
        replacement = self._replacement
        if self._has_parameters():
            parameters = tokens.extract_parameters(self._parameters)
            replacement = self._substitute(parameters)
        interpreter.typeset(replacement)

    def _has_parameters(self):
        return self._parameters != [""]

    def _substitute(self, parameters):
        body = self._replacement
        for (key, value) in parameters.items():
            pattern = r"#%d" % key
            body = sub(pattern, value, body)
        return body

    def __eq__(self, other):
        if not isinstance(other, Macro): return False
        return other._name == self._name \
            and other._parameters == self._parameters \
            and other._replacement == self._replacement


class DefineMacro(Macro):

    def __init__(self):
        super().__init__("def", [], "")

    def evaluate(self, interpreter, tokens):
        macro = tokens.capture_macro_definition()
        interpreter.define(macro)


class TokenStream:

    def __init__(self, input_stream):
        self._stream = iter(input_stream)

    def __iter__(self):
       return self

    def __next__(self):
        return Token(next(self._stream))

    def prepend(self, text):
        self._stream = chain(iter(text), self._stream)

    def capture_macro_definition(self):
        assert next(self).starts_a_macro()
        macro_name = self._capture_macro_name()
        parameters = self.extract_macro_parameters()
        replacement = self.extract_replacement()
        assert next(self).ends_replacement()
        return Macro(macro_name, parameters, replacement)

    def _capture_macro_name(self):
        return self._extract_while(lambda token: token.belongs_to_the_macro_name())

    def extract_parameters(self, arguments):
        parameters = dict()
        for index in range(len(arguments)):
            each_argument = arguments[index]
            if each_argument.startswith("#"):
                key = int(each_argument[1:])
                if index+1 < len(arguments):
                    next_argument = arguments[index+1]
                    parameters[key] = self._extract_until_pattern(next_argument)
                else:
                    parameters[key] = self._extract_until(lambda token: token.starts_a_macro())
            else:
                self.extract(each_argument)
        return parameters

    def extract(self, text):
        for each_character in text:
            found = str(next(self))
            if each_character != found:
                raise UnexpectedToken(found, each_character)
        return text

    def _extract_while(self, shall_include):
        buffer = ""
        for any_token in self:
            if shall_include(any_token):
                buffer += str(any_token)
            else:
                self.prepend([str(any_token)])
                return buffer
        return buffer

    def _extract_until_pattern(self, pattern):
        buffer = ""
        for each_token in self:
            buffer += str(each_token)
            if buffer.endswith(pattern):
                self.prepend(pattern)
                return buffer[:len(buffer)-len(pattern)]
        raise UnexpectedToken(expected=pattern, actual="End of stream")

    def _extract_until(self, accept):
        if isinstance(accept, str):
            return self._extract_while(lambda token: str(token) != accept)
        if callable(accept):
            return self._extract_while(lambda token: not accept(token))
        return ValueError("Invalid type of acceptance criteria (found: %s)" % type(accept))

    def extract_comment(self):
        return self._extract_until("\n")

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


class Token:

    def __init__(self, character):
        self._character = character

    def _is(self, character):
        return self._character == character

    def starts_a_comment(self):
        return self._is("%")

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

    def __str__(self):
        return self._character


class TeXInterpreter:
    """
    Parse a TeX program
    """

    def __init__(self, environment, output):
        self._environment = environment
        self._output = output

    def typeset(self, text):
        self._output.write(text)

    def evaluate(self, input):
        tokens = TokenStream(input)
        for any_token in tokens:
            if any_token.starts_a_macro():
                macro = self._match_macro(tokens)
                macro.evaluate(self, tokens)
            elif any_token.starts_a_comment():
                self.typeset(str(any_token))
                comment = tokens.extract_comment()
                self.typeset(comment)
            else:
                self.typeset(str(any_token))

    def _match_macro(self, tokens):
        name = tokens._capture_macro_name()
        if name in self._environment:
            return self._environment[name]
        raise UnknownMacroException(name)

    def define(self, macro):
        self._environment[macro.name] = macro


class UnexpectedToken(Exception):

    def __init__(self, actual, expected):
        self._expected = expected
        self._actual = actual


class UnknownMacroException(Exception):

    def __init__(self, macro_name):
        self._macro_name = macro_name
