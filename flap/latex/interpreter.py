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


from flap.latex.commons import Context
from flap.latex.processor import Processor


class Interpreter(Processor):

    def __init__(self, tokens, factory, environment, name=None):
        super().__init__(name or "INTERPRETER",
                         tokens,
                         factory,
                         environment)

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
            self.process_invocation(invocation)

    def process_invocation(self, invocation):
        self._log("On invocation: " + invocation.as_text)
        macro = self.look_up(invocation.command_name)

        if macro.is_user_defined:
            self._log("User defined!")
            self.open_scope()
            for each_argument, tokens in invocation.arguments.items():
                self._log(f"Evaluating argument {each_argument}")
                evaluated = self.evaluate(tokens)
                self._definitions[each_argument] = evaluated
            self._log("Evaluating macro body")
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
        interpreter = Interpreter(self._tokens, self._create, definitions)
        for each_token in tokens:
            each_token.send_to(interpreter)
        return interpreter._output
        # return Interpreter(tokens,
        #                    self._create,
        #                    definitions).process()

    def evaluate_as_text(self, tokens):
        # interpreter = Interpreter(tokens, self._create, self._definitions)
        # return self._as_text(interpreter.process())
        evaluated = self.evaluate(tokens)
        return self._as_text(evaluated)
