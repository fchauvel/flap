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
from flap.latex.commons import Context
from flap.util import truncate


class Processor:

    def __init__(self, name, tokens, factory, environment):
        self._create = factory
        self._tokens = self._create.as_stream(tokens)
        self._definitions = environment
        self._level = 0
        self._name = name
        # Outputs
        self._outputs = [{"is_active": True, "data": []}]

    def process(self):
        while not self._tokens.is_empty:
            token = self._tokens.take()
            token.send_to(self)
        self._log("----------- DONE")
        return self._outputs[-1]["data"]

    def process_control(self, token):
        self._default(token)

    def process_begin_group(self, token):
        self._default(token)

    def process_end_group(self, end_group):
        self._default(end_group)

    def process_character(self, character):
        self._default(character)

    def process_comment(self, comment):
        self._default(comment)

    def process_parameter(self, parameter):
        self._default(parameter)

    def process_white_spaces(self, space):
        self._default(space)

    def process_new_line(self, new_line):
        self._default(new_line)

    def process_others(self, other):
        self._default(other)

    def process_invocation(self, invocation):
        self._default(invocation)

    def _default(self, token):
        self._log("On " + str(token))
        self._print([token])

    # Helpers

    # Debugging

    def _log(self, message):
        logger.debug(self._name + ": " + message)

    # Methods that manage the output

    def _print(self, tokens):
        if self._outputs[-1]["is_active"]:
            self._outputs[-1]["data"] += tokens

    def push_new_output(self):
        self._log("Setup new output")
        new_output = {"is_active": True, "data": []}
        self._outputs.append(new_output)

    def pop_output(self):
        self._log("Discarding current output: " + self.output_as_text())
        output = self._outputs.pop()
        return output["data"]

    def output_as_text(self):
        return "".join(each_token.as_text
                       for each_token in self._outputs[-1]["data"])

    # Scope and look up

    def open_scope(self):
        self._definitions = Context(self._definitions)

    def close_scope(self):
        self._definitions = self._definitions._parent

    def look_up(self, symbol):
        return self._definitions.look_up(symbol)

    def find_environment(self, invocation):
        symbol = "".join(each_token.as_text
                         for each_token
                         in invocation.argument("environment")[1:-1])
        environment = self._definitions.look_up(symbol)
        return environment

    def _debug(self, category, action, tokens):
        text = ""
        position = "None"
        if not len(tokens) == 0:
            text = truncate(self._as_text(tokens), 30)
            position = tokens[-1].location,
        logger.debug(
                "GL={} {} {} {}".format(
                    self._level,
                    action,
                    category,
                    text
                ))

    @staticmethod
    def _as_text(tokens):
        return "".join(map(str, tokens))
