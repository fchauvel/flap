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


class Parser:

    def __init__(self, lexer, output, engine):
        self._lexer = lexer
        self._tokens = None
        self._output = output
        self._engine = engine

    def parse(self, text):
        self._tokens = Stream(self._lexer.tokens_from(text), Token.white_space("\0"))
        next_token = self._tokens.look_ahead()
        while next_token != Token.white_space("\0"):
            next_token.accept(self)
            self._tokens.take()
            next_token = self._tokens.look_ahead()

    def dump(self, text):
        self._output.write(text)

    def invoke_command(self, command):
        if command == "\input":
            self._process_input()
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
