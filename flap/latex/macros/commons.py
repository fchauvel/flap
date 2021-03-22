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

from flap import logger
from flap.latex.errors import UnknownSymbol


class Macro:
    """
    A LaTeX macro, including its name (e.g., 'point'), its signature
    as a list of expected tokens (e.g., '(#1,#2)') and the text that
    should replace it.
    """

    def __init__(self, flap, name, signature, body):
        self._flap = flap
        self._name = name if not name.startswith("\\") else name[1:]
        self._signature = signature or []
        self._body = body or iter([])
        self._called = False
        self._requires_expansion = False
        self.is_user_defined = False

    @property
    def requires_expansion(self):
        return self._requires_expansion

    @property
    def was_called(self):
        return self._called

    @property
    def name(self):
        return self._name

    def execute2(self, parser, invocation):
        self._called = True
        pass

    def rewrite2(self, parser, invocation):
        return invocation.as_tokens

    def capture_invocation(self, parser, command):
        invocation = Invocation(command)
        self._capture_arguments(parser, invocation)
        return invocation

    def _capture_arguments(self, parser, invocation):
        for index, any_token in enumerate(self._signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(self._signature) - 1:
                    expression = parser.read.one()
                    invocation.append_argument(parameter, expression)
                    logger.debug("Arg '{}' is '{}'".format(
                        any_token.as_text,
                        "".join(t.as_text for t in expression)))
                else:
                    next_token = self._signature[index + 1]
                    value = parser.read.until_text(next_token.as_text)
                    invocation.append_argument(parameter, value)
                    logger.debug("Arg '{}' is '{}'".format(
                        any_token.as_text,
                        "".join(t.as_text for t in value)))
            else:
                invocation.append(parser.read.text(str(any_token)))

    def expand(self, invocation):
        # TODO: Remove, useless as the we don't substitute tokens into
        # the body anymore
        result = []
        for any_token in self._body:
            if any_token.is_a_parameter:
                result += invocation.argument(str(any_token))
            else:
                result.append(any_token)
        return result

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
        self.is_user_defined = True


class UpdateLink(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    @staticmethod
    def _capture_arguments(parser, invocation):
        invocation.append_argument("options", parser.read.options())
        logger.debug("Options = '%s'", invocation.argument_as_text("options"))
        invocation.append_argument("link", parser.read.group())

    def execute2(self, parser, invocation):
        pass

    def rewrite2(self, parser, invocation):
        try:
            link_tokens = invocation.argument("link")
            link = parser.evaluate_as_text(invocation.argument("link"))
            new_link = self.update_link(parser, link, invocation)
            opening = str(link_tokens[0])
            closing = str(link_tokens[-1])
            return invocation\
                .substitute("link",
                            parser._create.as_list(opening + new_link + closing))\
                .as_tokens
        except UnknownSymbol:
            return invocation.as_tokens

    def update_link(self, parser, link, invocation):
        """To be over-ridden in sub classes"""
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


class Invocation:
    """ The invocation of a LaTeX command, including the name of the
    command, and its parameters indexed by name as sequences of
    tokens.
    """

    def __init__(self, command):
        self.name = command
        self._arguments = []
        self._keys = dict()

    @property
    def as_text(self):
        text = self.to_text(self.name)
        for each_argument in self._arguments:
            text += "".join(map(str, each_argument))
        return text

    @staticmethod
    def to_text(parameter):
        if isinstance(parameter, list):
            return "".join(map(Invocation.to_text, parameter))
        elif isinstance(parameter, str):
             return parameter
        else:
            return parameter.as_text

    @property
    def command_name(self):
        """Returns the name (as a string) of the command without the first
        control character.
        """
        return str(self.name)[1:]

    def send_to(self, parser):
        return parser.process_invocation(self)

    def append(self, tokens):
        self._arguments.append(tokens)

    def append_argument(self, name, value):
        self._arguments.append(value)
        self._keys[name] = len(self._arguments) - 1

    def argument(self, key):
        return self._arguments[self._keys[key]]

    def argument_as_text(self, key):
        return "".join(each_token.as_text
                       for each_token in self.argument(key))

    @property
    def location(self):
        assert self.as_tokens, \
            "Could not fetch invocation's position '%s'" % self.as_text
        return self.as_tokens[0].location

    @property
    def arguments(self):
        return {key: self._arguments[value]
                for (key, value) in self._keys.items()}


    @property
    def as_tokens(self):
        start = copy(self.name) \
            if isinstance(self.name, list) \
            else [self.name]
        return sum(self._arguments, start)

    def substitute(self, argument, value):
        clone = Invocation(self.name)
        clone.name = copy(self.name)
        clone._arguments = copy(self._arguments)
        clone._keys = copy(self._keys)
        clone._arguments[clone._keys[argument]] = value
        return clone
