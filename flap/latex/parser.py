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
from flap.latex.tokens import Token, TokenFactory


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
        return parser.parse_call(self._name, self._signature, self._body)

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

    def __init__(self):
        self._definitions = dict()

    def __setitem__(self, key, value):
        self._definitions[key] = value

    def __getitem__(self, macro_name):
        return self._definitions.get(macro_name)

    def __contains__(self, macro_name):
        assert isinstance(macro_name, str), \
            "Invalid macro name. Expected string, but found '{0}' object instead.".format(type(macro_name))
        return macro_name in self._definitions


class Parser:

    def __init__(self, lexer, engine, environment):
        self._lexer = lexer
        self._tokens = None
        self._symbols = TokenFactory(self._lexer.symbols)
        self._engine = engine
        self._definitions = environment

    def _spawn(self):
        return Parser(self._lexer, self._engine, self._definitions)

    def parse(self, tokens):
        result = []
        self._tokens = Stream(iter(tokens), self._symbols.end_of_text())
        while not self._next_token.ends_the_text:
            result += self._next_token.accept(self)
        return result

    @property
    def _next_token(self):
        return self._tokens.look_ahead()

    def evaluate_parameter(self, parameter):
        self._tokens.take()
        return self._definitions[parameter]

    def default(self, text):
        return [self._tokens.take()]

    def define_macro(self, name, signature, replacement):
        self._definitions[name] = Macro(name, signature, replacement)
        return []

    def parse_call(self, macro, signature, body):
        self._accept(self._symbols.command(macro))
        self._parse_arguments(signature)
        return self._spawn().parse(body[1:-1])

    def _accept(self, expected_token):
        next_token = self._tokens.look_ahead()
        if next_token != expected_token:
            raise ValueError("Expecting %s but found %s" % (expected_token, next_token))
        else:
            return self._tokens.take()

    def _parse_arguments(self, signature):
        for index, any_token in enumerate(signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(signature)-1:
                    self._definitions[parameter] = self._read_one()
                else:
                    next_token = signature[index + 1]
                    self._definitions[parameter] = self._read_until(next_token)
            else:
                self._accept(any_token)

    def _read_one(self):
        result = []
        next_token = self._tokens.look_ahead()
        self._abort_on_end_of_text(next_token)
        if next_token.begins_a_group:
            result += self._parse_group()
        elif next_token.is_a_command:
            self.invoke_command(str(next_token))
        elif next_token.is_a_parameter:
            result += self._definitions[str(next_token)]
            self._tokens.take()
        else:
            result.append(next_token)
            self._tokens.take()
        return result

    def _parse_group(self):
        self._accept(self._symbols.begin_group())
        result = self._read_until(self._symbols.end_group())
        self._accept(self._symbols.end_group())
        return result

    def _read_until(self, end_marker):
        result = []
        next_token = self._tokens.look_ahead()
        while next_token != end_marker:
            result += self._read_one()
            next_token = self._tokens.look_ahead()
        return result

    @staticmethod
    def _abort_on_end_of_text(token):
        if token.ends_the_text:
            raise ValueError("Unexpected end of string!")

    def evaluate_command(self, command):
        if command == r"\input":
            return self._process_input()
        elif command == r"\def":
            return self._process_definition()
        else:
            if command in self._definitions:
                macro = self._definitions[command]
                return macro.parse_with(self)
            else:
                return self.default(command)

    def _process_input(self):
        self._tokens.take()  # the command name
        self._tokens.take_while(lambda c: c.is_a_whitespace)
        next_token = self._tokens.look_ahead()
        if next_token.is_a_character:
            file_name = "".join(str(t) for t in self._tokens.take_while(lambda c: c.is_a_character))
            content = self._engine.content_of(file_name)
            return [self._symbols.character(content)]

    def _process_definition(self):
        self._tokens.take()
        name = self._tokens.take()
        signature = self._tokens.take_while(lambda t: not t.begins_a_group)
        body = self._capture_group()
        return self.define_macro(str(name), signature, body)

    def _capture_group(self):
        tokens = []
        tokens.append(self._accept(self._symbols.begin_group()))
        while not self._tokens.look_ahead().ends_a_group:
            tokens += self._capture_one()
        tokens.append(self._accept(self._symbols.end_group()))
        return tokens

    def _capture_one(self):
        tokens = []
        next_token = self._tokens.look_ahead()
        self._abort_on_end_of_text(next_token)
        if next_token.begins_a_group:
            tokens += self._capture_group()
        else:
            tokens.append(next_token)
            self._tokens.take()
        return tokens
