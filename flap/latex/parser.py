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


from flap.latex.tokens import Token, TokenCategory
from flap.latex.lexer import Stream


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


class Parser:

    def __init__(self, lexer, output, engine):
        self._lexer = lexer
        self._tokens = None
        self._symbols = self._lexer.symbols
        self._output = output
        self._engine = engine
        self._environment = dict()

    def parse(self, text):
        self._tokens = Stream(self._lexer.tokens_from(text), self._symbols.end_of_text())
        next_token = self._tokens.look_ahead()
        while next_token != self._end_of_text():
            next_token.accept(self)
            self._tokens.take()
            next_token = self._tokens.look_ahead()

    def _end_of_text(self):
        return self._symbols.end_of_text()

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
        for (index, any_token) in enumerate(signature):
            if any_token.is_a(TokenCategory.PARAMETER):
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
            if next_token.is_a(TokenCategory.BEGIN_GROUP):
                result += self._parse_group()
            else:
                result.append(next_token)
                self._tokens.take()
            next_token = self._tokens.look_ahead()
        return result

    def _abort_on_end_of_text(self, token):
        if token == self._end_of_text():
            raise ValueError("Unexpected end of string!")

    @staticmethod
    def _substitute(arguments, body):
        for argument, tokens in arguments.items():
            value = ''.join([str(each_token) for each_token in tokens])
            body = body.replace(argument, value)
        return body

    def dump(self, text):
        self._output.write(text)

    def invoke_command(self, command):
        if command == "\input":
            self._process_input()
        else:
            if command in self._environment:
                macro = self._environment[command]
                macro.parse_with(self)
            else:
                self.dump(command)

    def _process_input(self):
        self._tokens.take()  # the command name
        self._take_zero_or_more(TokenCategory.WHITE_SPACE)
        next_token = self._tokens.look_ahead()
        if next_token.is_a(TokenCategory.CHARACTER):
            file_name = self._take_zero_or_more(TokenCategory.CHARACTER)
            content = self._engine.content_of(file_name)
            self.dump(content)

    def _take_zero_or_more(self, category):
        return self._tokens.take_while(lambda token: token.is_a(category))