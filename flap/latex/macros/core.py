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

    def execute2(self, parser, invocation):
        body = invocation.argument("body")
        macro = UserDefinedMacro(
            self._flap,
            "".join(map(str, invocation.argument("name"))),
            invocation.argument("signature"),
            body)
        parser.define(macro)

    def rewrite2(self, parser, invocation):
        body = invocation.argument("body")
        try:
            rewritten_body = parser.rewrite(body, dict())

        except UnknownSymbol:
            rewritten_body = body

        return invocation.substitute("body", rewritten_body).as_tokens

    def rewrite(self, parser):
        invocation = self._parse(parser)
        self._execute(parser, invocation)
        return invocation.substitute("body", self._rewritten_body).as_tokens

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("name", parser.read.macro_name())
        invocation.append_argument("signature", parser.read.until_group())
        invocation.append_argument("body", parser.read.group())


class Begin(Macro):
    """
    A LaTeX environment such as \begin{center} \\end{center}.
    """

    def __init__(self, flap):
        super().__init__(flap, "begin", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("environment", parser.read.group())

    def execute2(self, parser, invocation):
        environment = parser.find_environment(invocation)
        if environment is None:
            return
        return environment.execute2(parser, invocation)

    def rewrite2(self, parser, invocation):
        environment = parser.find_environment(invocation)
        if environment is None:
            return invocation.as_tokens
        return environment.rewrite2(parser, invocation)


class DocumentClass(Macro):
    """
    Extract some specific document class, e.g., subfile
    """

    def __init__(self, flap):
        super().__init__(flap, "documentclass", None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.read.options())
        invocation.append_argument("class", parser.read.group())

    def execute2(self, parser, invocation):
        class_name = self.find_class_name(parser, invocation)
        self._flap.relocate_dependency(class_name, invocation)

    def find_class_name(self, parser, invocation):
        tokens = invocation.argument("class")
        return "".join(each_token.as_text
                       for each_token in tokens[1:-1])

    def rewrite2(self, parser, invocation):
        class_name = self.find_class_name(parser, invocation)
        if class_name == "subfiles":
            parser.read.until_text(r"\begin{document}", True)
            document = parser.read.until_text(r"\end{document}", True)
            logger.debug("Subfile extraction" +
                         "".join(str(t) for t in document))
            return parser.evaluate(document[:-11], dict())
        return invocation.as_tokens


class PackageReference(Macro):
    """Abstract commands that load a package, either locally or from
    those installed with LaTeX (e.g., usepackage or RequirePackage).
    """

    def __init__(self, flap, name):
        super().__init__(flap, name, None, None)

    def _capture_arguments(self, parser, invocation):
        invocation.append_argument("options", parser.read.
                                   options())
        invocation.append_argument("package", parser.read.one())

    def execute2(self, parser, invocation):
        pass

    def rewrite2(self, parser, invocation):
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
