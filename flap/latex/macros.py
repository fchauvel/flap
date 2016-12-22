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

import re
from copy import copy


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


class MacroFactory:
    """
    Create macros that are associated with a given FLaP backend
    """

    def __init__(self, flap):
        self._flap = flap
        self._macros = [
            DocumentClass(self._flap),
            UsePackage(self._flap),
            RequirePackage(self._flap),
            Input(self._flap),
            Include(self._flap),
            IncludeOnly(self._flap),
            Bibliography(self._flap),
            BibliographyStyle(self._flap),
            SubFile(self._flap),
            IncludeGraphics(self._flap),
            GraphicsPath(self._flap),
            Def(self._flap),
            Begin(self._flap),
            MakeIndex(self._flap)]

    def all(self):
        return {each.name: each for each in self._macros}

    def create(self, name, parameters, body):
        return Macro(self._flap, name, parameters, body)


class Macro:
    """
    A LaTeX macro, including its name (e.g., '\point'), its signature as a list
    of expected tokens (e.g., '(#1,#2)') and the text that should replace it.
    """

    def __init__(self, flap, name, signature, body):
        self._flap = flap
        self._name = name
        self._signature = signature
        self._body = body

    @property
    def name(self):
        return self._name

    def invoke(self, parser):
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
        signature, body = "", ""
        if signature:
            signature = "".join(map(str, self._signature))
        if body:
            body = "".join(map(str, self._body))
        return r"\def" + self._name + signature + body


class Begin(Macro):
    """
    A LaTeX environment such as \begin{center} \end{center}.
    """

    def __init__(self, flap):
        super().__init__(flap, r"\begin", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("environment", parser.capture_group())

    def _execute(self, parser, invocation):
        environment = parser.evaluate_as_text(invocation.argument("environment"))
        if environment == "verbatim":
            return parser._create.as_list(r"\begin{verbatim}") + parser.capture_until_text(r"\end{verbatim}")
        else:
            return invocation.as_tokens


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self, flap):
        super().__init__(flap, r"\documentclass", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("class", parser.capture_group())

    def _execute(self, parser, invocation):
        class_name = parser.evaluate_as_text(invocation.argument("class"))
        self._flap.relocate_dependency(class_name, invocation)
        if class_name == "subfiles":
            parser.capture_until_text(r"\begin{document}")
            document = parser.capture_until_text(r"\end{document}")
            return parser._spawn(document[:-11], dict()).rewrite()
        else:
            return invocation.as_tokens


class Def(Macro):

    def __init__(self, flap):
        super().__init__(flap, r"\def", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("name", parser.capture_macro_name())
        invocation.append_argument("signature", parser.capture_until_group())
        invocation.append_argument("body", parser.capture_group())

    def _execute(self, parser, invocation):
        macro = Macro(
            self._flap,
            "".join(map(str, invocation.argument("name"))),
            invocation.argument("signature"),
            invocation.argument("body"))
        parser.define(macro)
        return []


class PackageReference(Macro):
    """
    Abstract commands that load a package, either locally or from those installed
    with LaTeX (e.g., usepackage or RequirePackage).
    """

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("package", parser.capture_one())

    def _execute(self, parser, invocation):
        package = parser.evaluate_as_text(invocation.argument("package"))
        self._flap.relocate_dependency(package, invocation)
        return invocation.as_tokens


class UsePackage(PackageReference):
    """
    Intercept 'usepackage' commands. It triggers copying the package, if it is
    defined locally.
    """

    def __init__(self, flap):
        super().__init__(flap, r"\usepackage")


class RequirePackage(PackageReference):
    """
    Intercept 'RequirePackage' commands. It triggers copying the package, if it is
    defined locally.
    """

    def __init__(self, flap):
        super().__init__(flap, r"\RequirePackage")


class MakeIndex(Macro):
    """
    Intercept 'makeindex' commands. It triggers copying the index style file,
    if they are it can be found locally.
    """

    def __init__(self, flap):
        super().__init__(flap, r"\makeindex", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())

    def _execute(self, parser, invocation):
        style_file = self._fetch_style_file(parser, invocation)
        new_style_file = self._flap.update_link_to_index_style(style_file, invocation)
        return invocation.as_text.replace(style_file, new_style_file)

    @staticmethod
    def _fetch_style_file(parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("options"))
        for each in text.strip()[1:-1].split(","):
            _, value = each.split("=")
            options = re.split("(-\w\s)", value)
            for index in range(len(options)):
                if "-s" in options[index]:
                    return options[index+1]
        return None


class TexFileInclusion(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("link", parser.capture_one())

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        content = self._flap.content_of(link, invocation)
        return parser._spawn(parser._create.as_tokens(content, link), dict()).rewrite()


class Input(TexFileInclusion):
    """
    Intercept the `\input` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\input")


class Include(TexFileInclusion):
    """
    Intercept the `\include` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\include")

    def _execute(self, parser, invocation):
        link = parser.evaluate_as_text(invocation.argument("link"))
        if self._flap.shall_include(link):
            result = super()._execute(parser, invocation)
            return result + parser._create.as_list(r"\clearpage")
        return []


class SubFile(TexFileInclusion):

    def __init__(self, flap):
        super().__init__(flap, r"\subfile")


class IncludeOnly(Macro):
    """
    Intercept includeonly commands
    """

    def __init__(self, flap):
        super().__init__(flap, r"\includeonly", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("selection", parser.capture_one())

    def _execute(self, parser, invocation):
        text = parser.evaluate_as_text(invocation.argument("selection"))
        files_to_include = list(map(str.strip, text.split(",")))
        self._flap.include_only(files_to_include, invocation)
        return []


class UpdateLink(Macro):

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    @staticmethod
    def _capture_arguments(parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("link", parser.capture_group())

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

    def __init__(self, flap):
        super().__init__(flap, r"\includegraphics")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link(link, invocation)


class Bibliography(UpdateLink):
    """
    Intercept the `\bibliography` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\bibliography")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link_to_bibliography(link, invocation)


class BibliographyStyle(UpdateLink):
    """
    Intercept the `\bibliographystyle` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\bibliographystyle")

    def update_link(self, parser, link, invocation):
        return self._flap.update_link_to_bibliography_style(link, invocation)


class GraphicsPath(Macro):
    """
    Intercept the `\graphicspath` directive
    """

    def __init__(self, flap):
        super().__init__(flap, r"\graphicspath", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("paths", parser.capture_group())

    def _execute(self, parser, invocation):
        argument = parser.evaluate_as_text(invocation.argument("paths"))
        paths = list(map(str.strip, argument.split(",")))
        self._flap.record_graphic_path(paths, invocation)
        return invocation.as_tokens
