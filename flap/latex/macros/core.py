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
from flap.latex.macros.commons import Macro, UserDefinedMacro
from flap.latex.errors import UnknownSymbol
from flap.latex.symbols import SymbolTable
from flap.latex.parser import Factory

factory = Factory(SymbolTable.default())


class CatCode(Macro):

    def __init__(self, flap):
        super().__init__(flap,
                         "catcode",
                         factory.as_list("#1=#2\n"),
                         None)

    def _execute(self, parser, invocation):
        logger.debug("Invocation: " + invocation.as_text)
        character = "".join(str(each_token)
                            for each_token
                            in invocation.argument("#1"))

        if character[0] == "`":
            if character[1] == "\\":
                character = character[2]
            else:
                character = character[1]

        new_category = "".join(str(each_token)
                               for each_token
                               in invocation.argument("#2"))

        self._flap.set_character_category(character, int(new_category))
        return invocation.as_tokens


class Def(Macro):

    def __init__(self, flap):
        super().__init__(flap, "def", None, None)

    def rewrite(self, parser):
        invocation = self._parse(parser)
        self._execute(parser, invocation)
        return invocation.substitute("body", self._rewritten_body).as_tokens

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("name", parser.capture_macro_name())
        invocation.append_argument("signature", parser.capture_until_group())
        invocation.append_argument("body", parser.capture_group())

    def _execute(self, parser, invocation):
        body = invocation.argument("body")
        try:
            self._rewritten_body = parser._spawn(body, dict()).rewrite()
        except UnknownSymbol:
            self._rewritten_body = body

        macro = UserDefinedMacro(
            self._flap,
            "".join(map(str, invocation.argument("name"))),
            invocation.argument("signature"),
            body)
        parser.define(macro)
        return []


class Begin(Macro):
    """
    A LaTeX environment such as \begin{center} \\end{center}.
    """

    def __init__(self, flap):
        super().__init__(flap, "begin", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("environment", parser.capture_group())

    def _execute(self, parser, invocation):
        environment = parser.evaluate_as_text(
            invocation.argument("environment"))
        env = parser._definitions.look_up(environment)
        if env:
            logger.debug("Known environment " + environment)
            return env.execute(parser, invocation)
        logger.debug("Unknown environment " + environment)
        return invocation.as_tokens


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self, flap):
        super().__init__(flap, "documentclass", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("class", parser.capture_group())

    def _execute(self, parser, invocation):
        class_name = parser.evaluate_as_text(invocation.argument("class"))
        self._flap.relocate_dependency(class_name, invocation)
        if class_name == "subfiles":
            parser.capture_until_text(r"\begin{document}", True)
            document = parser.capture_until_text(r"\end{document}", True)
            logger.debug("Subfile extraction" + "".join(str(t) for t in document))
            return parser._spawn(document[:-11], dict()).rewrite()
        else:
            return invocation.as_tokens


class PackageReference(Macro):
    """Abstract commands that load a package, either locally or from
    those installed with LaTeX (e.g., usepackage or RequirePackage).
    """

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.capture_options())
        invocation.append_argument("package", parser.capture_one())

    def _execute(self, parser, invocation):
        package = parser.evaluate_as_text(invocation.argument("package"))
        new_link = self._flap.relocate_dependency(package, invocation)
        if new_link:
            return invocation.substitute(
                "package",
                parser._create.as_list("{" + new_link + "}")
            ).as_tokens
        return invocation.as_tokens


class UsePackage(PackageReference):
    """
    Intercept 'usepackage' commands. It triggers copying the package,
    if it is defined locally.
    """

    def __init__(self, flap):
        super().__init__(flap, "usepackage")


class RequirePackage(PackageReference):
    """
    Intercept 'RequirePackage' commands. It triggers copying the
    package, if it is defined locally.
    """

    def __init__(self, flap):
        super().__init__(flap, "RequirePackage")
