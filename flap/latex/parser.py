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
        self._replacement = replacement

    def parse_with(self, parser):
        parser.parse_call(self._name, self._signature, self._replacement)

    def __eq__(self, other):
        if not isinstance(other, Macro):
            return False
        return self._name == other._name and \
               self._signature == other._signature and \
               self._replacement == other._replacement

    def __repr__(self):
        signature = "".join([str(t) for t in self._signature])
        return r"\def" + self._name + signature + "{" + self._replacement + "}"


class Parser:

    def __init__(self, lexer, output, engine):
        self._lexer = lexer
        self._tokens = None
        self._symbols = TokenFactory(self._lexer.symbols)
        self._output = output
        self._engine = engine
        self._environment = dict()

    def parse(self, text):
        self._tokens = Stream(self._lexer.tokens_from(text), self._symbols.end_of_text())
        next_token = self._tokens.look_ahead()
        while not next_token.ends_the_text:
            next_token.accept(self)
            self._tokens.take()
            next_token = self._tokens.look_ahead()

    def define_macro(self, name, signature, replacement):
        self._environment[name] = Macro(name, signature, replacement)

    def parse_call(self, macro, signature, body):
        self._accept(self._symbols.command(macro))
        arguments = self._parse_arguments(signature)
        replacement = self._substitute(arguments, body)
        self.dump(replacement)

    def _accept(self, expected_token):
        next_token = self._tokens.look_ahead()
        if next_token != expected_token:
            raise ValueError("Expecting %s but found %s" % (expected_token, next_token))
        else:
            self._tokens.take()

    def _parse_arguments(self, signature):
        arguments = dict()
        for index, any_token in enumerate(signature):
            if any_token.is_a_parameter:
                if index == len(signature)-1:
                    arguments[str(any_token)] = self._read_until(self._symbols.begin_group())
                else:
                    next_token = signature[index + 1]
                    arguments[str(any_token)] = self._read_until(next_token)
            else:
                self._accept(any_token)
        return arguments

    def _parse_group(self):
        self._accept(self._symbols.begin_group())
        result = self._read_until(self._symbols.end_group())
        self._accept(self._symbols.end_group())
        return result

    def _read_until(self, end_marker):
        result = []
        next_token = self._tokens.look_ahead()
        while next_token != end_marker:
            self._abort_on_end_of_text(next_token)
            if next_token.begins_a_group:
                result += self._parse_group()
            else:
                result.append(next_token)
                self._tokens.take()
            next_token = self._tokens.look_ahead()
        return result

    @staticmethod
    def _abort_on_end_of_text(token):
        if token.ends_the_text:
            raise ValueError("Unexpected end of string!")

    @staticmethod
    def _substitute(arguments, body):
        for argument, tokens in arguments.items():
            value = ''.join([str(each_token) for each_token in tokens])
            body = body.replace(argument, value)
        return body

    def dump(self, *texts):
        for each_text in texts:
            if isinstance(each_text, str):
                self._output.write(each_text)
            elif isinstance(each_text, Token):
                self._output.write(str(each_text))
            elif isinstance(each_text, list):
                self.dump(*each_text)

    def invoke_command(self, command):
        if command == "\input":
            self._process_input()
        elif command == r"\def":
            self._process_definition()
        else:
            if command in self._environment:
                macro = self._environment[command]
                macro.parse_with(self)
            else:
                self.dump(command)

    def _process_input(self):
        self._tokens.take()  # the command name
        self._tokens.take_while(lambda c: c.is_a_whitespace)
        next_token = self._tokens.look_ahead()
        if next_token.is_a_character:
            file_name = "".join(str(t) for t in self._tokens.take_while(lambda c: c.is_a_character))
            content = self._engine.content_of(file_name)
            self.dump(content)

    def _process_definition(self):
        define = self._tokens.take()
        name = self._tokens.take()
        signature = self._tokens.take_while(lambda t: not t.begins_a_group)
        body = self._parse_group()
        self.dump(define, name, signature, self._symbols.begin_group(), body, self._symbols.end_group())
        self._environment[str(name)] = Macro(str(name), signature, ''.join(str(t) for t in body))

