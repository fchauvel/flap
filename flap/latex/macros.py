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


class Invocation:
    """
    The invocation of a LaTeX command, including the name of the command, and its
    parameters indexed by name.
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
        text = "".join(str(each) for each in self.name)
        for each_argument in self._arguments:
            text += "".join(str(each) for each in each_argument)
        return text

    @property
    def as_tokens(self):
        tokens = copy(self.name)
        for each_argument in self._arguments:
            tokens += each_argument
        return tokens

    def substitute(self, argument, value):
        clone = Invocation()
        clone.name = copy(self.name)
        clone._arguments = copy(self._arguments)
        clone._keys = copy(self._keys)
        clone._arguments[clone._keys[argument]] = value
        return clone



class Macro:
    """
    A LaTeX macro, including its name (e.g., '\point'), its signature as a list
    of expected tokens (e.g., '(#1,#2)') and the text that should replace it.
    """

    def __init__(self, name, signature, body):
        self._name = name
        self._signature = signature
        self._body = body

    def invoke(self, parser):
        invocation = self._parse(parser)
        return self._execute(parser, invocation)

    def _parse(self, parser):
        invocation = Invocation()
        self._capture_name(invocation, parser)
        self._capture_arguments(parser, invocation)
        return invocation

    def _capture_name(self, invocation, parser):
        invocation.name = parser._accept(lambda token: token.is_a_command and token.has_text(self._name))
        extra_spaces = parser._tokens.take_while(lambda c: c.is_ignored)
        invocation.append(extra_spaces)

    def _capture_arguments(self, parser, invocation):
        for index, any_token in enumerate(self._signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(self._signature)-1:
                    invocation.append_argument(parameter, parser._evaluate_one())
                else:
                    next_token = self._signature[index + 1]
                    value = parser._evaluate_until(lambda token: token.has_text(next_token._text))
                    invocation.append_argument(parameter, value)
            else:
                invocation.append(parser._accept(lambda token: True))

    def _execute(self, parser, invocation):
        return parser._spawn(self._body, invocation.arguments)._evaluate_group()

    def __eq__(self, other):
        if not isinstance(other, Macro):
            return False
        return self._name == other._name and \
               self._signature == other._signature and \
               self._body == other._body

    def __repr__(self):
        signature = "".join(str(each_token) for each_token in self._signature)
        body = "".join(str(each_token) for each_token in self._body)
        return r"\def" + self._name + signature + body


class Begin(Macro):
    """
    A LaTeX environment such as \begin{center} \end{center}.
    """

    def __init__(self):
        super().__init__(r"\begin", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("environment", parser._capture_group())

    def _execute(self, parser, invocation):
        environment = parser.evaluate_as_text(invocation.argument("environment"))
        if environment == "verbatim":
            return parser._create.as_list(r"\begin{verbatim}") + parser._capture_until(r"\end{verbatim}")
        else:
            return invocation.as_tokens


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self):
        super().__init__(r"\documentclass", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.optional_arguments())
        invocation.append_argument("class", parser._capture_group())

    def _execute(self, parser, invocation):
        class_name = parser.evaluate_as_text(invocation.argument("class"))
        if class_name == "subfiles":
            parser._capture_until(r"\begin{document}")
            document = parser._capture_until(r"\end{document}")
            return parser._spawn(document[:-11], dict()).rewrite()
        else:
            return invocation.as_tokens


class Def(Macro):

    def __init__(self):
        super().__init__(r"\def", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("name", parser._tokens.take())
        invocation.append_argument("signature", parser._tokens.take_while(lambda t: not t.begins_a_group))
        invocation.append_argument("body", parser._capture_group())

    def _execute(self, parser, invocation):
        return parser.define_macro(
            str(invocation.argument("name")),
            invocation.argument("signature"),
            invocation.argument("body"))


class TexFileInclusion(Macro):

    def __init__(self, name):
        super().__init__(name, None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("link", parser._capture_one())

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        content = parser._engine.content_of(link, invocation)
        return parser._spawn(parser._create.as_tokens(content, link), dict()).rewrite()


class Input(TexFileInclusion):
    """
    Intercept the `\input` directive
    """

    def __init__(self):
        super().__init__(r"\input")


class Include(TexFileInclusion):
    """
    Intercept the `\include` directive
    """

    def __init__(self):
        super().__init__(r"\include")

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        if parser._engine.shall_include(link):
            result = super()._execute(parser, invocation)
            return result + parser._create.as_list(r"\clearpage")
        return []


class SubFile(TexFileInclusion):

    def __init__(self):
        super().__init__(r"\subfile")


class IncludeOnly(Macro):
    """
    Intercept includeonly commands
    """

    def __init__(self):
        super().__init__(r"\includeonly", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("selection", parser._capture_one())

    def _execute(self, parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("selection"))
        files_to_include = [each.strip() for each in text.split(",")]
        parser._engine.include_only(files_to_include, invocation)
        return []


class UpdateLink(Macro):

    def __init__(self, name):
        super().__init__(name, None, None)

    @staticmethod
    def _capture_arguments(parser, invocation):
        invocation.append_argument("options", parser.optional_arguments())
        invocation.append_argument("link", parser._capture_group())

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        new_link = self.update_link(parser, link, invocation)
        return invocation.substitute("link", parser._create.as_list("{" + new_link + "}")).as_tokens

    def update_link(self, parser, link, invocation):
        pass


class IncludeGraphics(UpdateLink):
    """
    Intercept the `\includegraphics` directive
    """

    def __init__(self):
        super().__init__(r"\includegraphics")

    def update_link(self, parser, link, invocation):
        return parser._engine.update_link(link, invocation)


class Bibliography(UpdateLink):
    """
    Intercept the `\includegraphics` directive
    """

    def __init__(self):
        super().__init__(r"\bibliography")

    def update_link(self, parser, link, invocation):
        return parser._engine.update_link_to_bibliography(link, invocation)


class GraphicsPath(Macro):

    def __init__(self):
        super().__init__(r"\graphicspath", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("paths", parser._capture_group())

    def _execute(self, parser, invocation):
        paths = parser.evaluate_as_text(invocation.argument("paths"))
        parser._engine.record_graphic_path([each.strip() for each in paths.split(",")], invocation)
        return invocation.as_tokens