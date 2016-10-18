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

from flap.latex.commons import Stream
from flap.latex.lexer import Lexer


class Macro:
    """
    A LaTeX macro, including its name (e.g., '\point'), its signature as a list of expected tokens (e.g., '(#1,#2)')
    and the text that should replace it.
    """

    def __init__(self, name, signature, replacement):
        self._name = name
        self._signature = signature
        self._body = replacement

    @property
    def name(self):
        return self._name

    def parse_with(self, parser):
        return parser.evaluate_macro(self._name, self._signature, self._body)

    def __eq__(self, other):
        if not isinstance(other, Macro):
            return False
        return self._name == other._name and \
               self._signature == other._signature and \
               self._body == other._body

    def __repr__(self):
        signature = "".join(str(each_token) for each_token in self._signature)
        body = "".join(str(each_token) for each_token in self._body)
        return r"\def" + self._name + signature + body


class Environment:

    def __init__(self, parent=None):
        self._definitions = dict()
        self._parent = parent

    def fork(self):
        return Environment(self)

    def __setitem__(self, key, value):
        self._definitions[key] = value

    def __getitem__(self, key):
        if self._parent and key not in self._definitions:
            return self._parent[key]
        else:
            return self._definitions.get(key)

    def __contains__(self, key):
        return key in self._definitions or (self._parent and key in self._parent)


class Factory:

    def __init__(self, symbols):
        self._symbols = symbols

    def as_tokens(self, text):
        return Lexer(self._symbols, text)

    def as_list(self, text):
        return list(Lexer(self._symbols, text))

    def as_stream(self, tokens):
        return Stream(tokens)


class Parser:

    def __init__(self, tokens, factory, engine, environment):
        self._create = factory
        self._engine = engine
        self._tokens = self._create.as_stream(tokens)
        self._definitions = environment
        self._filters = {r"\input": self._process_input,
                         r"\def": self._process_definition,
                         r"\begin": self._process_environment}

    def _spawn(self, tokens, environment):
        return Parser(
            tokens,
            self._create,
            self._engine,
            environment)

    def rewrite(self):
        result = []
        while not self._tokens.is_empty:
            result += self._rewrite_one()
        return result

    def _rewrite_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._capture_group()
        elif self._next_token.is_a_command:
            return self._evaluate_one()
        else:
            return [self._tokens.take()]

    @property
    def _next_token(self):
        return self._tokens.look_ahead()

    def default(self, text):
        return [self._tokens.take()]

    def define_macro(self, name, signature, replacement):
        self._definitions[name] = Macro(name, signature, replacement)
        return []

    def evaluate_macro(self, name, signature, body):
        self._accept(lambda token: token.is_a_command and token.has_text(name))
        environment = self._evaluate_arguments(signature)
        return self._spawn(body, environment)._evaluate_group()

    def _accept(self, as_expected):
        if not as_expected(self._next_token):
            raise ValueError("Unexpected token %s!" % self._next_token)
        else:
            return self._tokens.take()

    def evaluate_parameter(self, parameter):
        self._tokens.take()
        return self._definitions[parameter]

    def _evaluate_arguments(self, signature):
        environment = self._definitions.fork()
        for index, any_token in enumerate(signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(signature)-1:
                    environment[parameter] = self._evaluate_one()
                else:
                    next_token = signature[index + 1]
                    environment[parameter] = self._evaluate_until(lambda token: token.has_text(next_token._text))
            else:
                self._accept(lambda token: True)
        return environment

    def _evaluate_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._evaluate_group()
        elif self._next_token.is_a_command:
            return self.evaluate_command(str(self._next_token))
        elif self._next_token.is_a_parameter:
            return self._definitions[str(self._tokens.take())]
        else:
            return [self._tokens.take()]

    def _evaluate_group(self):
        self._accept(lambda token: token.begins_a_group)
        tokens = self._evaluate_until(lambda token: token.ends_a_group)
        self._accept(lambda token: token.ends_a_group)
        return tokens

    def _evaluate_until(self, is_excluded):
        result = []
        while not is_excluded(self._next_token):
            result += self._evaluate_one()
        return result

    def _abort_on_end_of_text(self):
        if self._tokens.is_empty:
            raise ValueError("Unexpected end of text!")

    def evaluate_command(self, command):
        if command in self._definitions:
            macro = self._definitions[command]
            return macro.parse_with(self)
        elif command in self._filters:
            return self._filters[command]()
        else:
            return self.default(command)

    def _process_input(self):
        self._tokens.take()  # the command name
        self._tokens.take_while(lambda c: c.is_a_whitespace)
        argument = self._evaluate_one()
        file_name = self._as_text(argument)
        content = self._engine.content_of(file_name)
        return self._spawn(self._create.as_tokens(content), Environment()).rewrite()

    @staticmethod
    def _as_text(tokens):
        return "".join(str(each) for each in tokens)

    def _process_definition(self):
        self._tokens.take()
        name = self._tokens.take()
        signature = self._tokens.take_while(lambda t: not t.begins_a_group)
        body = self._capture_group()
        return self.define_macro(str(name), signature, body)

    def _process_environment(self):
        begin = self._tokens.take()
        environment = self._capture_group()
        if self._as_text(environment) == "{verbatim}":
            return [begin] + environment + self._capture_until(r"\end{verbatim}")
        else:
            return [begin] + environment

    def _capture_until(self, expected_text):
        read = []
        while self._next_token:
            read.append(self._tokens.take())
            text_read = "".join(str(token) for token in read)
            if text_read.endswith(expected_text):
                break
        return read

    def _capture_group(self):
        tokens = [self._accept(lambda token: token.begins_a_group)]
        while not self._next_token.ends_a_group:
            tokens += self._capture_one()
        tokens.append(self._accept(lambda token: token.ends_a_group))
        return tokens

    def _capture_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._capture_group()
        else:
            return [self._tokens.take()]
