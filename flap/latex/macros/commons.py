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

from copy import copy

from flap.latex.errors import UnknownSymbol


class Macro:
    """
    A LaTeX macro, including its name (e.g., '\point'), its signature as a list
    of expected tokens (e.g., '(#1,#2)') and the text that should replace it.
    """

    def __init__(self, flap, name, signature, body):
        self._flap = flap
        self._name = name
        self._signature = signature or []
        self._body = body or iter([])
        self._called = False
        self._requires_expansion = False

    @property
    def requires_expansion(self):
        return self._requires_expansion

    @property
    def was_called(self):
        return self._called

    @property
    def name(self):
        return self._name

    def rewrite(self, parser):
        invocation = self._parse(parser)
        return self._execute(parser, invocation)

    def evaluate(self, parser):
        self._called = True
        invocation = self._parse(parser)
        return self._execute(parser, invocation)

    def _parse(self, parser):
        invocation = Invocation()
        self._capture_name(invocation, parser)
        self._capture_arguments(parser, invocation)
        return invocation

    def _capture_name(self, invocation, parser):
        invocation.name = parser.capture_macro_name(self._name)
        invocation.append(parser.capture_ignored())

    def _capture_arguments(self, parser, invocation):
        for index, any_token in enumerate(self._signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(self._signature)-1:
                    expression = parser.capture_one()
                    invocation.append_argument(parameter, expression)
                else:
                    next_token = self._signature[index + 1]
                    value = parser._evaluate_until(lambda token: token.has_text(next_token._text))
                    invocation.append_argument(parameter, value)
            else:
                invocation.append(parser._accept(lambda token: True))

    def _execute(self, parser, invocation):
        arguments = { parameter: parser._spawn(argument, dict()).evaluate() for parameter, argument in invocation.arguments.items() }
        return parser._spawn(self._body, arguments)._evaluate_group()

    def __eq__(self, other):
        if not isinstance(other, Macro):
            return False
        return self._name == other._name and \
               self._signature == other._signature and \
               self._body == other._body

    def __repr__(self):
        signature, body = "", ""
        if signature:
            signature = "".join(map(str, self._signature))
        if body:
            body = "".join(map(str, self._body))
        return r"\def" + self._name + signature + body


class UserDefinedMacro(Macro):

    def __init__(self, flap, name, signature, body):
        super().__init__(flap, name, signature, body)

    def rewrite(self, parser):
        invocation = self._parse(parser)
        expansion = super()._execute(parser, invocation)
        if parser.shall_expand():
            return expansion
        return invocation.as_tokens


class UpdateLink(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    @staticmethod
    def _capture_arguments(parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("link", parser.capture_group())

    def _execute(self, parser, invocation):
        try:
            link = parser.evaluate_as_text(invocation.argument("link"))
            new_link = self.update_link(parser, link, invocation)
            return invocation.substitute("link", parser._create.as_list("{" + new_link + "}")).as_tokens
        except UnknownSymbol:
            return invocation.as_tokens

    def update_link(self, parser, link, invocation):
        pass


class Environment:
    """
    Represent LaTeX environments, such as \begin{center} for instance.
    """

    def __init__(self, flap, name):
        self._flap = flap
        self._name = name

    @property
    def name(self):
        return self._name

    @staticmethod
    def execute(self, parser, invocation):
        return []


class Invocation:
    """
    The invocation of a LaTeX command, including the name of the command, and its
    parameters indexed by name as sequences of tokens.
    """

    def __init__(self):
        self.name = []
        self._arguments = []
        self._keys = dict()

    def append(self, tokens):
        self._arguments.append(tokens)

    def append_argument(self, name, value):
        self._arguments.append(value)
        self._keys[name] = len(self._arguments) - 1

    def argument(self, key):
        return self._arguments[self._keys[key]]

    @property
    def location(self):
        assert self.as_tokens, "Could not fetch invocation's position '%s'" % self.as_text
        return self.as_tokens[0].location

    @property
    def arguments(self):
        return {key:self._arguments[value] for (key, value) in self._keys.items()}

    @property
    def as_text(self):
        text = "".join(map(str, self.name))
        for each_argument in self._arguments:
            text += "".join(map(str, each_argument))
        return text

    @property
    def as_tokens(self):
        return sum(self._arguments, copy(self.name))

    def substitute(self, argument, value):
        clone = Invocation()
        clone.name = copy(self.name)
        clone._arguments = copy(self._arguments)
        clone._keys = copy(self._keys)
        clone._arguments[clone._keys[argument]] = value
        return clone
