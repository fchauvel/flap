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
from flap.latex.macros import *


class Context:

    def __init__(self, parent=None):
        self._definitions = dict()
        self._parent = parent

    def fork(self):
        return Context(self)

    def extend_with(self, other):
        if isinstance(other, dict):
            for key, value in other.items():
                self._definitions[key] = value
        elif isinstance(other, Context):
            for key, value in other._definitions.items():
                self._definitions[key] = value
        else:
            raise ValueError("Expecting either 'Context' or a 'dict', but found a '%s' instead." % type(other))

    def items(self):
        return self._definitions.items()

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
        self._set_builtin_definitions()

    def _set_builtin_definitions(self):
        self._definitions[r"\input"] = Input()
        self._definitions[r"\include"] = Include()
        self._definitions[r"\includegraphics"] = IncludeGraphics()
        self._definitions[r"\graphicspath"] = GraphicsPath()
        self._definitions[r"\def"] = Def()
        self._definitions[r"\begin"] = Begin()

    def _spawn(self, tokens, environment):
        new_environment = Context(self._definitions)
        new_environment.extend_with(environment)
        return Parser(
            tokens,
            self._create,
            self._engine,
            new_environment)

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

    def _accept(self, as_expected):
        if not as_expected(self._next_token):
            error = "Unexpected {} '{}' at line {}, column {}.".format(
                self._next_token._category.name,
                self._next_token,
                self._next_token.location.line,
                self._next_token.location.column
            )
            raise ValueError(error)
        else:
            return self._tokens.take()

    def evaluate_parameter(self, parameter):
        self._tokens.take()
        return self._definitions[parameter]

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
            return macro.invoke(self)
        else:
            return self.default(command)

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

    @staticmethod
    def _as_text(tokens):
        return "".join(str(each) for each in tokens)

