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
        arguments = self._parse(parser)
        return self._execute(parser, arguments)

    def _parse(self, parser):
        parser._accept(lambda token: token.is_a_command and token.has_text(self._name))
        parser._tokens.take_while(lambda c: c.is_a_whitespace)
        return self._evaluate_arguments(parser)

    def _evaluate_arguments(self, parser):
        environment = dict()
        for index, any_token in enumerate(self._signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(self._signature)-1:
                    environment[parameter] = parser._evaluate_one()
                else:
                    next_token = self._signature[index + 1]
                    environment[parameter] = parser._evaluate_until(lambda token: token.has_text(next_token._text))
            else:
                parser._accept(lambda token: True)
        return environment

    def _execute(self, parser, arguments):
        return parser._spawn(self._body, arguments)._evaluate_group()

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

    def _evaluate_arguments(self, parser):
        arguments = dict()
        arguments["environment"] = parser._as_text(parser._evaluate_group())
        return arguments

    def _execute(self, parser, arguments):
        if arguments["environment"] == "verbatim":
            return parser._create.as_list(r"\begin{verbatim}") + parser._capture_until(r"\end{verbatim}")
        else:
            return parser._create.as_list(r"\begin{" + arguments["environment"] + "}")


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self):
        super().__init__(r"\documentclass", None, None)

    def _evaluate_arguments(self, parser):
        arguments = dict()
        arguments["options"] = parser.optional_arguments()
        arguments["class"] = parser._evaluate_group()
        return arguments

    def _execute(self, parser, arguments):
        class_name = parser._as_text(arguments["class"])
        if class_name == "subfile":
            parser._capture_until(r"\begin{document}")
            document = parser._capture_until(r"\end{document}")
            return parser._spawn(document[:-11], dict()).rewrite()
        else:
            return parser._create.as_list(r"\documentclass") + \
                   arguments["options"] + \
                   parser._create.as_list("{") + \
                   arguments["class"] + \
                   parser._create.as_list("}")


class Def(Macro):

    def __init__(self):
        super().__init__(r"\def", None, None)

    def _evaluate_arguments(self, parser):
        arguments = dict()
        arguments["name"] = parser._tokens.take()
        arguments["signature"] = parser._tokens.take_while(lambda t: not t.begins_a_group)
        arguments["body"] = parser._capture_group()
        return arguments

    def _execute(self, parser, arguments):
        return parser.define_macro(
            str(arguments["name"]),
            arguments["signature"],
            arguments["body"]
        )


class TexFileInclusion(Macro):

    def __init__(self, name):
        super().__init__(name, None, None)

    def _evaluate_arguments(self, parser):
        arguments = dict()
        arguments["link"] = parser._as_text(parser._evaluate_one())
        return arguments

    def _execute(self, parser, arguments):
        latex_command = self._name + "{" + parser._as_text(arguments["link"]) + "}"
        content = parser._engine.content_of(arguments["link"], latex_command)
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

    def _execute(self, parser, arguments):
        if parser._engine.shall_include(arguments["link"]):
            result = super()._execute(parser, arguments)
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

    def _evaluate_arguments(self, parser):
        arguments = dict()
        list_as_text = parser._as_text(parser._evaluate_one())
        arguments["selection"] = [part.strip() for part in list_as_text.split(",")]
        return arguments

    def _execute(self, parser, arguments):
        parser._engine.include_only(arguments["selection"])
        return []


class IncludeGraphics(Macro):
    """
    Intercept the `\includegraphics` directive
    """

    def __init__(self):
        super().__init__(r"\includegraphics", None, None)

    @staticmethod
    def _evaluate_arguments(parser):
        arguments = dict()
        arguments["options"] = parser.optional_arguments()
        arguments["link"] = parser._as_text(parser._evaluate_group())
        return arguments

    def _execute(self, parser, arguments):
        latex_command = self._format(arguments, parser)
        new_link = parser._engine.update_link(arguments["link"], latex_command)
        return parser._create.as_list(self._name) + arguments["options"] \
               + parser._create.as_list("{" + new_link + "}")

    def _format(self, arguments, parser):
        return self._name + parser._as_text(
            arguments["options"]) + "{" + parser._as_text(
            arguments["link"]) + "}"


class GraphicsPath(Macro):

    def __init__(self):
        super().__init__(r"\graphicspath", None, None)

    def _evaluate_arguments(self, parser):
        arguments = dict()
        path_tokens = parser._capture_group()
        arguments["path"] = parser._spawn(path_tokens, dict())._evaluate_one()
        return arguments

    def _execute(self, parser, arguments):
        path = parser._as_text(arguments["path"])
        parser._engine.record_graphic_path(path)
        return parser._create.as_list(self._name + "{{" + path + "}}")