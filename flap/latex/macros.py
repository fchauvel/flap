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


from collections import OrderedDict


class Invocation:
    """
    The invocation of a LaTeX command, including the name of the command, and its
    parameters indexed by name.
    """

    def __init__(self):
        self.name = None
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
    def arguments(self):
        return {key:self._arguments[value] for (key, value) in self._keys.items()}

    @property
    def as_text(self):
        text = str(self.name)
        for each_argument in self._arguments:
            text += "".join(str(each) for each in each_argument)
        return text


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
        invocation.name = parser._accept(lambda token: token.is_a_command and token.has_text(self._name))
        invocation.append(parser._tokens.take_while(lambda c: c.is_a_whitespace))
        self._evaluate_arguments(parser, invocation)
        return invocation

    def _evaluate_arguments(self, parser, invocation):
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

    def _evaluate_arguments(self, parser, invocation):
        invocation.append_argument("environment", parser._as_text(parser._evaluate_group()))

    def _execute(self, parser, invocation):
        if invocation.argument("environment") == "verbatim":
            return parser._create.as_list(r"\begin{verbatim}") + parser._capture_until(r"\end{verbatim}")
        else:
            return parser._create.as_list(r"\begin{" + invocation.argument("environment") + "}")


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self):
        super().__init__(r"\documentclass", None, None)

    def _evaluate_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.optional_arguments())
        invocation.append_argument("class", parser._evaluate_group())

    def _execute(self, parser, invocation):
        class_name = parser._as_text(invocation.argument("class"))
        if class_name == "subfile":
            parser._capture_until(r"\begin{document}")
            document = parser._capture_until(r"\end{document}")
            return parser._spawn(document[:-11], dict()).rewrite()
        else:
            return parser._create.as_list(r"\documentclass") + \
                   invocation.argument("options") + \
                   parser._create.as_list("{") + \
                   invocation.argument("class") + \
                   parser._create.as_list("}")


class Def(Macro):

    def __init__(self):
        super().__init__(r"\def", None, None)

    def _evaluate_arguments(self, parser, invocation):
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

    def _evaluate_arguments(self, parser, invocation):
        invocation.append_argument("link", parser._as_text(parser._evaluate_one()))

    def _execute(self, parser, invocation):
        link = invocation.argument("link")
        latex_command = self._name + "{" + link + "}"
        content = parser._engine.content_of(link, latex_command)
        return parser._spawn(parser._create.as_tokens(content), dict()).rewrite()


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
        if parser._engine.shall_include(invocation.argument("link")):
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

    def _evaluate_arguments(self, parser, invocation):
        list_as_text = parser._as_text(parser._evaluate_one())
        invocation.append_argument("selection", [part.strip() for part in list_as_text.split(",")])

    def _execute(self, parser, invocation):
        parser._engine.include_only(invocation.argument("selection"))
        return []


class IncludeGraphics(Macro):
    """
    Intercept the `\includegraphics` directive
    """

    def __init__(self):
        super().__init__(r"\includegraphics", None, None)

    @staticmethod
    def _evaluate_arguments(parser, invocation):
        invocation.append_argument("options", parser.optional_arguments())
        invocation.append_argument("link", parser._capture_group())

    def _execute(self, parser, invocation):
        link = parser._as_text(parser._spawn(invocation.argument("link"), dict())._evaluate_one())
        new_link = parser._engine.update_link(link, invocation.as_text)
        return parser._create.as_list(self._name) + invocation.argument("options") \
               + parser._create.as_list("{" + new_link + "}")


class GraphicsPath(Macro):

    def __init__(self):
        super().__init__(r"\graphicspath", None, None)

    def _evaluate_arguments(self, parser, invocation):
        path_tokens = parser._capture_group()
        invocation.append_argument("path", parser._spawn(path_tokens, dict())._evaluate_one())

    def _execute(self, parser, invocation):
        path = parser._as_text(invocation.argument("path"))
        parser._engine.record_graphic_path(path)
        return parser._create.as_list(self._name + "{{" + path + "}}")