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
from flap.latex.commons import Context, Stream, Source
from flap.latex.lexer import Lexer
from flap.latex.processor import Processor


class Factory:

    def __init__(self, symbols):
        self._symbols = symbols

    def as_tokens(self, text, name):
        return Lexer(self._symbols, Source.with_name(text, name))

    def as_list(self, text):
        return list(Lexer(self._symbols, Source.anonymous(text)))

    def as_stream(self, tokens):
        return Stream(tokens)


class Parser(Processor):

    def __init__(self, tokens, factory, environment):
        super().__init__("REWRITER", tokens, factory, environment)

    def process_control(self, token):
        self._log("On command:" + str(token))
        command = str(token)
        command_name = command[1:]
        if command_name not in self._definitions:
            self._log("Unknown command '{}'.\n"
                      "\tCandidates are {}"
                      .format(command_name,
                              self._definitions.available_macros))
            self._print([token])
        else:
            macro = self._definitions[command_name]
            invocation = macro.capture_invocation(self, token)
            self._log(invocation.as_text)
            self._tokens.push(invocation)

    def process_invocation(self, invocation):
        self._log("On invocation: " + invocation.as_text)
        macro = self.look_up(invocation.command_name)

        if macro.is_user_defined:
            self._log("User defined!")
            self.open_scope()
            for each_argument, tokens in invocation.arguments.items():
                evaluated = self.evaluate(tokens)
                self._definitions[each_argument] = evaluated
            self.evaluate(macro._body)
            self.close_scope()

        else:   # Built-in commands
            self._log("Built-in!")
            macro.execute2(self, invocation)

        self._print(macro.rewrite2(self, invocation))

    @property
    def _next_token(self):
        next_token = self._tokens.look_ahead()
        return next_token

    def define(self, macro):
        self._definitions.define(macro)

    def flush(self, source_name):
        while self._next_token \
              and self._next_token.location.source == source_name:
            self._tokens.take()

    def _raise_unexpected_token(self):
        error = (
            "Unexpected {} '{}' in file {} (line {}, column {})"
        ).format(
            self._next_token._category.name,
            self._next_token,
            self._next_token.location.source,
            self._next_token.location.line,
            self._next_token.location.column)
        self._tokens.debug()
        raise ValueError(error)

    @property
    def read(self):
        reader = Reader("", self._create)
        reader._tokens = self._tokens
        return reader

    def rewrite(self, tokens, extra_definitions=None):
        definitions = self._definitions
        if extra_definitions:
            definitions = Context(self._definitions, extra_definitions)
        return Parser(tokens, self._create, definitions).process()

    def evaluate(self, tokens, extra_definitions=None):
        definitions = self._definitions
        if extra_definitions:
            definitions = Context(self._definitions, extra_definitions)
        return Interpreter(tokens, self._create, definitions).process()

    def evaluate_as_text(self, tokens):
        interpreter = Interpreter(tokens, self._create, self._definitions)
        return self._as_text(interpreter.process())

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


class Interpreter(Parser):

    def __init__(self, tokens, factory, environment):
        super().__init__(tokens, factory, environment)
        self._name = "INTERPRETER"

    def process_begin_group(self, token):
        pass

    def process_end_group(self, end_group):
        pass

    def process_parameter(self, parameter):
        tokens = self.look_up(parameter.as_text)
        if tokens is not None:
            self._tokens.push(tokens)
        else:
            raise RuntimeError(f"Undefined symbol '{str(parameter)}'")

    def process_invocation(self, invocation):
        self._log("On invocation: " + invocation.as_text)
        macro = self.look_up(invocation.command_name)

        if macro.is_user_defined:
            self._log("User defined!")
            self.open_scope()
            for each_argument, tokens in invocation.arguments.items():
                evaluated = self.evaluate(tokens)
                self._definitions[each_argument] = evaluated
            output = self.evaluate(macro._body)
            self._print(output)
            self.close_scope()

        else:   # Built-in commands
            self._log("Built-in!")
            macro.execute2(self, invocation)

    def evaluate(self, tokens, extra_definitions=None):
        definitions = self._definitions
        if extra_definitions:
            definitions = Context(self._definitions, extra_definitions)
        return Interpreter(tokens, self._create, definitions).process()

    def evaluate_as_text(self, tokens):
        interpreter = Interpreter(tokens, self._create, self._definitions)
        return self._as_text(interpreter.process())



class Reader(Parser):

    def __init__(self, tokens, factory):
        super().__init__(tokens, factory, dict())
        self._name = "READER"

    def one(self):
        self._log("Reading one ...")
        if not self._tokens.is_empty:
            token = self._tokens.take()
            token.send_to(self)
            return self._outputs[-1]["data"]
        return None

    def group(self):
        self._log("Reading group ...")
        self.until(lambda t: not t.is_ignored)
        self.only_if(lambda t: t.begins_a_group)
        return self._outputs[-1]["data"]

    def only_if(self, is_expected):
        self._log("Reading only if  ...")
        if not self._tokens.is_empty:
            token = self._tokens.take()
            if is_expected(token):
                token.send_to(self)
            else:
                self._tokens.push(token)
                self._raise_unexpected_token("not specified", token)

    def until(self, is_end):
        self._log("Reading until ...")
        while not self._tokens.is_empty:
            token = self._tokens.take()
            if is_end(token):
                self._tokens.push(token)
                break
            else:
                token.send_to(self)
        return self._outputs[-1]["data"]

    def until_group(self):
        self.until(lambda t: t.begins_a_group)
        return self._outputs[-1]["data"]

    def options(self, start="[", end="]"):
        self._log("Reading options ...")
        try:
            self.until(lambda t: not t.is_ignored)
            self.only_if(lambda token: token.has_text(start))
            self.until_text(end)
            self.only_if(lambda token: token.has_text(end))
            self.until(lambda t: not t.is_ignored)
            return self._outputs[-1]["data"]
        except ValueError as error:
            self._log("Error '%s'" % str(error))
            return []

    def macro_name(self, name=None):
        self.only_if(lambda token: token.is_a_command)
        if name and not self._outputs[-1]["data"][-1].ends_with(name):
            self._raise_unexpected_token()
        return self._outputs[-1]["data"]

    def ignored(self):
        while self._next_token \
              and self._next_token.is_ignored:
            token = self._tokens.take()
            token.send_to(self)
        return self._outputs[-1]["data"]

    def text(self, marker):
        self._log("Reading text '%s'" % marker)
        text = ""
        while self._next_token:
            token = self._tokens.take()
            text += str(token)
            if not marker.startswith(text):
                self._tokens.push(token)
                break
            token.send_to(self)
        return self._outputs[-1]["data"]

    def until_text(self, marker, capture_marker=False):
        self._log("Reading until text '%s' ..." % marker)
        text = ""
        while self._next_token:
            token = self._tokens.take()
            text += str(token)
            if text.endswith(marker):
                if capture_marker:
                    self._print([token])
                else:
                    self._tokens.push(token)
                break
            self._print([token])
        return self._outputs[-1]["data"]

    def _raise_unexpected_token(self, expected, actual):
        error = (
            "Expected {}, but found '{}' in file {} (l. {}, col. {})"
        ).format(
            expected,
            actual,
            actual.location.source,
            actual.location.line,
            actual.location.column)
        self._tokens.debug()
        raise ValueError(error)

    def _default(self, token):
        self._print([token])

    def process_control(self, token):
        self._default(token)

    def process_begin_group(self, token):
        self._log("On begin group")
        self.push_new_output()
        self._print([token])
        self.until(lambda t: t.ends_a_group)
        self.only_if(lambda t: t.ends_a_group)

    def process_end_group(self, end_group):
        self._log("On end group")
        self._print([end_group])
        group_tokens = self.pop_output()
        self._print(group_tokens)

    def process_invocation(self, invocation):
        raise RuntimeError("Reader should never meet an invocation token!")
