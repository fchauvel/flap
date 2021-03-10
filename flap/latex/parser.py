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

from flap import logger
from flap.latex.commons import Stream, Source
from flap.latex.lexer import Lexer
from flap.latex.errors import UnknownSymbol
from flap.util import truncate

class Context:

    def __init__(self, parent=None, definitions=None):
        self._definitions = definitions or dict()
        self._parent = parent

    def look_up(self, symbol):
        result = self._definitions.get(symbol, None)
        if not result and self._parent:
            return self._parent.look_up(symbol)
        return result

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
        return key in self._definitions or (
            self._parent and key in self._parent)


class Factory:

    def __init__(self, symbols):
        self._symbols = symbols

    def as_tokens(self, text, name):
        return Lexer(self._symbols, Source.with_name(text, name))

    def as_list(self, text):
        return list(Lexer(self._symbols, Source.anonymous(text)))

    def as_stream(self, tokens):
        return Stream(tokens)


class Parser:

    def __init__(self, tokens, factory, environment):
        self._create = factory
        self._tokens = self._create.as_stream(tokens)
        self._definitions = environment
        self._level = 0

    def _spawn(self, tokens, environment):
        new_environment = Context(self._definitions,
                                  definitions=environment)
        parser = Parser(
            tokens,
            self._create,
            new_environment)
        return parser

    def look_up(self, symbol):
        return self._definitions.look_up(symbol)

    def rewrite(self):
        result = []
        while not self._tokens.is_empty:
            result += self._rewrite_one()
        return result

    def _rewrite_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._rewrite_group()
        elif self._next_token.is_a_command:
            return self._rewrite_command()
        else:
            return [self._tokens.take()]

    def _rewrite_group(self):
        self._level += 1
        tokens = self._accept(lambda token: token.begins_a_group)
        while not self._next_token.ends_a_group:
            tokens += self._rewrite_one()
        tokens += self._accept(lambda token: token.ends_a_group)
        self._debug("group", "rewritten", tokens)
        self._level -= 1
        return tokens

    def _rewrite_command(self):
        command = str(self._next_token)
        if command not in self._definitions:
            return self.default(command)
        macro = self._definitions[command]
        return macro.rewrite(self)

    @property
    def _next_token(self):
        next_token = self._tokens.look_ahead()
        return next_token

    def default(self, text):
        return [self._tokens.take()]

    def define(self, macro):
        self._definitions[macro.name] = macro

    def flush(self, source_name):
        while self._next_token \
              and self._next_token.location.source == source_name:
            self._tokens.take()

    def _accept(self, as_expected):
        buffer = self.capture_ignored()
        if as_expected(self._next_token):
            buffer.append(self._tokens.take())
            return buffer
        self._raise_unexpected_token()

    def _raise_unexpected_token(self):
        error = "Unexpected {} '{}' in file {} (line {}, column {})."\
        .format(
            self._next_token._category.name,
            self._next_token,
            self._next_token.location.source,
            self._next_token.location.line,
            self._next_token.location.column)
        raise ValueError(error)

    def evaluate_parameter(self, parameter):
        self._tokens.take()
        if parameter not in self._definitions:
            raise UnknownSymbol(parameter)
        return self._definitions[parameter]

    def evaluate_as_text(self, tokens):
        return self._as_text(self._spawn(tokens, dict()).evaluate())

    def evaluate(self):
        result = []
        while not self._tokens.is_empty:
            result += self._evaluate_one()
        return result

    def _evaluate_one(self):
        self._abort_on_end_of_text()
        if self._next_token.is_a_comment:
            self._tokens.take()
            return []
        if self._next_token.begins_a_group:
            return self._evaluate_group()
        elif self._next_token.is_a_command:
            return self.evaluate_command(str(self._next_token))
        elif self._next_token.is_a_parameter:
            parameter = str(self._tokens.take())
            if parameter in self._definitions:
                return self._definitions[parameter]
            raise UnknownSymbol(parameter)
        else:
            return [self._tokens.take()]

    def _evaluate_group(self):
        self._accept(lambda token: token.begins_a_group)
        tokens = self._evaluate_until(lambda token: token.ends_a_group)
        self._accept(lambda token: token.ends_a_group)
        self._debug("group", "evaluated", tokens)
        return tokens

    def _evaluate_until(self, is_excluded):
        tokens = []
        while not is_excluded(self._next_token):
            tokens += self._evaluate_one()
        return tokens

    def _abort_on_end_of_text(self):
        if self._tokens.is_empty:
            raise ValueError("Unexpected end of text!")

    def evaluate_command(self, command):
        if command not in self._definitions:
            return self.default(command)
        macro = self._definitions[command]
        return macro.evaluate(self)

    def capture_options(self, start="[", end="]"):
        result = []
        if self._next_token.has_text(start):
            result += self._accept(lambda token: token.has_text(start))
            result += self._evaluate_until(lambda token: token.has_text(end))
            result += self._accept(lambda token: token.has_text(end))
            result += self._tokens.take_while(lambda c: c.is_ignored)
        self._debug("options", "capture", result)
        return result

    def capture_macro_name(self, name=None):
        tokens = self._accept(lambda token: token.is_a_command)
        if name and not tokens[-1].has_text(name):
            self._raise_unexpected_token()
        self._debug("macro", "captured", tokens)
        return tokens

    def capture_ignored(self):
        tokens = []
        while self._next_token and self._next_token.is_ignored:
            tokens.append(self._tokens.take())
        return tokens

    def capture_until_text(self, marker):
        tokens, text = [], ""
        while self._next_token:
            text += str(self._next_token)
            tokens.append(self._tokens.take())
            if text.endswith(marker):
                break
        return tokens

    def capture_until_group(self):
        tokens = []
        while not self._next_token.begins_a_group:
            tokens += self.capture_one()
        return tokens

    def capture_group(self):
        tokens = self._accept(lambda token: token.begins_a_group)
        while not self._next_token.ends_a_group:
            tokens += self.capture_one()
        tokens += self._accept(lambda token: token.ends_a_group)
        self._debug("group", "captured", tokens)
        return tokens

    def capture_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self.capture_group()
        else:
            return [self._tokens.take()]

    @staticmethod
    def _as_text(tokens):
        return "".join(map(str, tokens))

    def shall_expand(self):
        logger.debug("Expanding")
        result = False
        for _, any_macro in self._definitions.items():
            was_called = getattr(any_macro, "was_called", None)
            if was_called \
               and any_macro.was_called \
               and any_macro.requires_expansion:
                result = True
        for _, any_macro in self._definitions.items():
            was_called = getattr(any_macro, "was_called", None)
            if was_called:
                any_macro._called = False
        return result

    def _debug(self, category, action, tokens):
        text = ""
        position = "None"
        if not len(tokens) == 0:
            text = truncate(self._as_text(tokens), 30)
            position = tokens[-1].location,
        logger.debug(
                "{} (GL={}) '{}' {} {}".format(
                    position,
                    self._level,
                    category,
                    action,
                    text
                ))
