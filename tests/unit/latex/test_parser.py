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

from unittest import TestCase, main
from unittest.mock import MagicMock, ANY

from flap.latex.symbols import SymbolTable
from flap.latex.tokens import TokenFactory
from flap.latex.macros.factory import MacroFactory
from flap.latex.parser import Parser, Context, Factory


class ContextTest(TestCase):

    def setUp(self):
        self._data = {"Z": 1}
        self._environment = Context()
        for key, value in self._data.items():
            self._environment[key] = value

    def test_look_up_a_key_that_was_never_defined(self):
        self.assertIsNone(self._environment["never defined"])
        self.assertNotIn("never defined", self._environment)

    def test_definition(self):
        (key, value) = ("X", 234)
        self.assertNotIn("X", self._environment)
        self._environment[key] = value
        self.assertEqual(value, self._environment[key])

    def test_containment(self):
        for key, value in self._data.items():
            self.assertTrue(key in self._environment)
            self.assertEqual(value, self._environment[key])


class ParserTests(TestCase):

    def setUp(self):
        self._engine = MagicMock()
        self._macros = MacroFactory(self._engine)
        self._symbols = SymbolTable.default()
        self._tokens = TokenFactory(self._symbols)
        self._factory = Factory(self._symbols)
        self._environment = Context(definitions=self._macros.all())
        self._lexer = None
        self._parser = None

    def test_parsing_a_regular_word(self):
        self._do_test_with("hello", "hello")

    def _do_test_with(self, collected, expected):
        parser = Parser(
            self._factory.as_tokens(
                collected,
                "Unknown"),
            self._factory,
            self._environment)
        tokens = parser.rewrite()
        self._verify_output_is(expected, tokens)

    def _verify_output_is(self, expected_text, actual_tokens):
        output = "".join(str(t) for t in actual_tokens)
        self.assertEqual(expected_text, output)

    def test_rewriting_a_group(self):
        self._do_test_with("{bonjour}",
                           "{bonjour}")

    def test_rewriting_a_command_that_shall_not_be_rewritten(self):
        self._do_test_with(r"\macro[option=23cm]{some text}",
                           r"\macro[option=23cm]{some text}")

    def test_rewriting_a_command_within_a_group(self):
        self._do_test_with(r"{\macro[option=23cm]{some text} more text}",
                           r"{\macro[option=23cm]{some text} more text}")

    def test_rewriting_a_command_in_a_verbatim_environment(self):
        self._do_test_with(r"\begin{verbatim}\foo{bar}\end{verbatim}",
                           r"\begin{verbatim}\foo{bar}\end{verbatim}")

    def test_rewriting_a_input_in_a_verbatim_environment(self):
        self._engine.content_of.return_value = "blabla"
        self._do_test_with(r"\begin{verbatim}\input{bar}\end{verbatim}",
                           r"\begin{verbatim}\input{bar}\end{verbatim}")
        self._engine.content_of.assert_not_called()

    def test_rewriting_a_unknown_environment(self):
        self._do_test_with(r"\begin{center}blabla\end{center}",
                           r"\begin{center}blabla\end{center}")

    def test_parsing_a_macro_definition(self):
        self._do_test_with(r"\def\myMacro#1{my #1}",
                           r"\def\myMacro#1{my #1}")

    def test_parsing_commented_out_input(self):
        self._do_test_with(r"% \input my-file",
                           r"% \input my-file")
        self._engine.content_of.assert_not_called()

    def test_invoking_a_macro_with_one_parameter(self):
        self._define_macro(r"\foo", "(#1)", "{bar #1}")
        self._do_test_with(r"\foo(1)", "bar 1")

    def _define_macro(self, name, parameters, body):
        macro = self._macro(name, parameters, body)
        self._environment[name] = macro

    def _macro(self, name, parameters, body):
        return self._macros.create(name, self._factory.as_list(
            parameters), self._factory.as_list(body))

    def test_defining_a_macro_without_parameter(self):
        self._do_test_with(r"\def\foo{X}",
                           r"\def\foo{X}")
        self.assertEqual(
            self._macro(
                r"\foo",
                "",
                "{X}"),
            self._environment[r"\foo"])

    def test_defining_a_macro_with_one_parameter(self):
        self._do_test_with(r"\def\foo#1{X}",
                           r"\def\foo#1{X}")
        self.assertEqual(
            self._macro(
                r"\foo",
                "#1",
                "{X}"),
            self._environment[r"\foo"])

    def test_defining_a_macro_with_multiple_parameters(self):
        self._do_test_with(r"\def\point(#1,#2,#3){X}",
                           r"\def\point(#1,#2,#3){X}")
        self.assertEqual(self._macro(r"\point", "(#1,#2,#3)", "{X}"),
                         self._environment[r"\point"])

    def test_parsing_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\input{my-file}",
                           r"File content")
        self._engine.content_of.assert_called_once_with("my-file", ANY)

    def test_rewriting_multiline_commands(self):
        self._engine.update_link_to_graphic.return_value = "img_result"
        self._do_test_with("\\includegraphics % \n" +
                           "[witdh=\\textwidth] % Blabla\n" +
                           "{img/result.pdf}",
                           "\\includegraphics % \n" +
                           "[witdh=\\textwidth] % Blabla\n" +
                           "{img_result}")
        self._engine.update_link_to_graphic\
            .assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_includegraphics(self):
        self._engine.update_link_to_graphic.return_value = "img_result"
        self._do_test_with(r"\includegraphics{img/result.pdf}",
                           r"\includegraphics{img_result}")
        self._engine.update_link_to_graphic\
                    .assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_includegraphics_with_parameters(self):
        self._engine.update_link_to_graphic.return_value = "img_result"
        self._do_test_with(
            r"\includegraphics[width=\linewidth]{img/result.pdf}",
            r"\includegraphics[width=\linewidth]{img_result}")
        self._engine.update_link_to_graphic\
                    .assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_graphicspath(self):
        self._do_test_with(r"\graphicspath{{img}}",
                           r"\graphicspath{{img}}")
        self._engine.record_graphic_path\
                    .assert_called_once_with(["img"], ANY)

    def test_rewriting_include(self):
        self._engine.shall_include.return_value = True
        self._engine.content_of.return_value = "File content"

        self._do_test_with(r"\include{my-file}",
                           r"File content\clearpage")

        self._engine.shall_include.assert_called_once_with("my-file")
        self._engine.content_of.assert_called_once_with("my-file", ANY)

    def test_rewriting_include_when_the_file_shall_not_be_included(self):
        self._engine.shall_include.return_value = False
        self._engine.content_of.return_value = "File content"

        self._do_test_with(r"\include{my-file}",
                           r"")

        self._engine.shall_include.assert_called_once_with("my-file")
        self._engine.content_of.assert_not_called()

    def test_rewriting_includeonly(self):
        self._engine.shall_include.return_value = True
        self._do_test_with(r"\includeonly{my-file.tex}",
                           r"")
        self._engine.include_only\
                    .assert_called_once_with(["my-file.tex"], ANY)

    def test_rewriting_subfile(self):
        self._engine.content_of.return_value \
            = r"\documentclass[../main.tex]{subfiles}" \
              r"" \
              r"\begin{document}" \
              r"File content" \
              r"\end{document}"

        self._do_test_with(r"\subfile{my-file}",
                           r"File content")

        self._engine.content_of.assert_called_once_with("my-file", ANY)

    def test_rewriting_document_class(self):
        self._do_test_with(r"\documentclass{article}"
                           r"\begin{document}"
                           r"Not much!"
                           r"\end{document}",
                           r"\documentclass{article}"
                           r"\begin{document}"
                           r"Not much!"
                           r"\end{document}")

        self._engine.relocate_dependency.assert_called_once_with(
            "article", ANY)

    def test_rewriting_usepackage(self):
        self._engine.relocate_dependency.return_value = None
        self._do_test_with(r"\usepackage{my-package}",
                           r"\usepackage{my-package}")

        self._engine.relocate_dependency.assert_called_once_with(
            "my-package", ANY)

    def test_rewriting_usepackage_that_exist_locally(self):
        self._engine.relocate_dependency.return_value = "style_my-package"
        self._do_test_with(r"\usepackage{style/my-package}",
                           r"\usepackage{style_my-package}")

        self._engine.relocate_dependency.assert_called_once_with(
            "style/my-package", ANY)

    def test_rewriting_usepackage_with_options(self):
        self._engine.relocate_dependency.return_value = None
        self._do_test_with(
            r"\usepackage[length=3cm,width=2cm]{my-package}",
            r"\usepackage[length=3cm,width=2cm]{my-package}")

        self._engine.relocate_dependency.assert_called_once_with(
            "my-package", ANY)

    def test_rewriting_bibliography_style(self):
        self._engine.update_link_to_bibliography_style\
                    .return_value = "my-style"
        self._do_test_with(r"\bibliographystyle{my-style}",
                           r"\bibliographystyle{my-style}")

        self._engine.update_link_to_bibliography_style.assert_called_once_with(
            "my-style", ANY)

    def test_rewriting_make_index(self):
        self._engine.update_link_to_index_style\
                    .return_value = "my-style.ist"
        self._do_test_with(
            "\\makeindex[columns=3, title=Alphabetical Index,\n"
            "options= -s my-style.ist]",
            "\\makeindex[columns=3, title=Alphabetical Index,\n"
            "options= -s my-style.ist]")

        self._engine.update_link_to_index_style.assert_called_once_with(
            "my-style.ist", ANY)

    def test_rewriting_endinput(self):
        self._do_test_with(
            r"foo \endinput bar",
            r"foo ")
        self._engine.end_of_input.assert_called_once_with("Unknown", ANY)

    def test_rewriting_overpic(self):
        self._engine.update_link_to_graphic.return_value = "img_result"
        self._do_test_with(
            r"\begin{overpic}{img/result}blabla\end{overpic}",
            r"\begin{overpic}{img_result}blabla\end{overpic}")
        self._engine.update_link_to_graphic\
                    .assert_called_once_with("img/result", ANY)

    def test_expanding_macros(self):
        self._engine.update_link_to_graphic.return_value = "images_logo"
        self._do_test_with(
            r"\def\logo{\includegraphics{images/logo}}"
            r"\logo",
            r"\def\logo{\includegraphics{images_logo}}"
            r"\logo"
        )


if __name__ == '__main__':
    main()
