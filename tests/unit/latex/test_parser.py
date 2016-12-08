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
from mock import MagicMock, ANY

from flap.latex.symbols import SymbolTable
from flap.latex.tokens import TokenFactory
from flap.latex.parser import Parser, Macro, Context, Factory


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

    def test_fork_and_look_up_key_defined_in_the_parent(self):
        fork = self._environment.fork()
        for key, value in self._data.items():
            self.assertTrue(key in fork)
            self.assertEqual(value, fork[key])

    def test_fork_and_redefine_key(self):
        fork = self._environment.fork()
        fork["Z"] = 2
        self.assertEqual(2, fork["Z"])
        self.assertEqual(1, self._environment["Z"])


class ParserTests(TestCase):

    def setUp(self):
        self._engine = MagicMock()
        self._symbols = SymbolTable.default()
        self._tokens = TokenFactory(self._symbols)
        self._factory = Factory(self._symbols)
        self._environment = Context()
        self._lexer = None
        self._parser = None

    def test_parsing_a_regular_word(self):
        self._do_test_with("hello", "hello")

    def _do_test_with(self, input, output):
        parser = Parser(self._factory.as_tokens(input, "Unknown"), self._factory, self._engine, self._environment)
        tokens = parser.rewrite()
        self._verify_output_is(output, tokens)

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
                           r"")

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
        return Macro(name, self._factory.as_list(parameters), self._factory.as_list(body))

    def test_invoking_a_macro_where_one_argument_is_a_group(self):
        self._define_macro(r"\foo", "(#1)", "{Text: #1}")
        self._do_test_with(r"\foo({bar!})",
                           r"Text: bar!")

    def test_invoking_a_macro_with_two_parameters(self):
        self._define_macro(r"\point", "(#1,#2)", "{X=#1 and Y=#2}")
        self._do_test_with(r"\point(12,{3 point 5})", "X=12 and Y=3 point 5")

    def test_defining_a_macro_without_parameter(self):
        self._do_test_with(r"\def\foo{X}",
                           r"")
        self.assertEqual(self._macro(r"\foo", "", "{X}"), self._environment[r"\foo"])

    def test_defining_a_macro_with_one_parameter(self):
        self._do_test_with(r"\def\foo#1{X}",
                           r"")
        self.assertEqual(self._macro(r"\foo", "#1", "{X}"), self._environment[r"\foo"])

    def test_defining_a_macro_with_multiple_parameters(self):
        self._do_test_with(r"\def\point(#1,#2,#3){X}",
                           r"")
        self.assertEqual(self._macro(r"\point", "(#1,#2,#3)", "{X}"),
                         self._environment[r"\point"])

    def test_macro(self):
        self._do_test_with(r"\def\foo{X}\foo",
                           r"X")

    def test_macro_with_one_parameter(self):
        self._do_test_with(r"\def\foo#1{x=#1}\foo{2}",
                           r"x=2")

    def test_macro_with_inner_macro(self):
        self._do_test_with(r"\def\foo#1{\def\bar#1{X #1} \bar{#1}} \foo{Y}",
                           r"  X Y")

    def test_macro_with_parameter_scope(self):
        self._do_test_with(r"\def\foo(#1,#2){"
                           r"\def\bar#1{Bar=#1}"
                           r"\bar{#2} ; #1"
                           r"}"
                           r"\foo(2,3)",
                           r"Bar=3 ; 2")

    def test_parsing_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\input{my-file}",
                           r"File content")
        self._engine.content_of.assert_called_once_with("my-file", ANY)

    def test_macro_with_inner_redefinition_of_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\def\foo#1{\def\input#1{File: #1} \input{#1}} \foo{test.tex}",
                           r"  File: test.tex")

    def test_macro_with_inner_use_of_input(self):
        self._engine.content_of.return_value = "blabla"
        self._do_test_with(r"\def\foo#1{File: \input{#1}} \foo{test.tex}",
                           r" File: blabla")

    def test_rewriting_multiline_commands(self):
        self._engine.update_link.return_value = "img_result"
        self._do_test_with("\\includegraphics % \n" +
                           "[witdh=\\textwidth] % Blabla\n" +
                           "{img/result.pdf}",
                           "\\includegraphics % \n" +
                           "[witdh=\\textwidth] % Blabla\n" +
                           "{img_result}")
        self._engine.update_link.assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_includegraphics(self):
        self._engine.update_link.return_value = "img_result"
        self._do_test_with(r"\includegraphics{img/result.pdf}",
                           r"\includegraphics{img_result}")
        self._engine.update_link.assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_includegraphics_with_parameters(self):
        self._engine.update_link.return_value = "img_result"
        self._do_test_with(r"\includegraphics[width=\linewidth]{img/result.pdf}",
                           r"\includegraphics[width=\linewidth]{img_result}")
        self._engine.update_link.assert_called_once_with("img/result.pdf", ANY)

    def test_rewriting_graphicspath(self):
        self._do_test_with(r"\graphicspath{{img}}",
                           r"\graphicspath{{img}}")
        self._engine.record_graphic_path.assert_called_once_with(["img"], ANY)

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
        self._engine.include_only.assert_called_once_with(["my-file.tex"], ANY)

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

        self._engine.relocate_class_file.assert_called_once_with("article", ANY)

    def test_rewriting_usepackage(self):
        self._do_test_with(r"\usepackage{my-package}",
                           r"\usepackage{my-package}")

        self._engine.relocate_package.assert_called_once_with("my-package", ANY)

    def test_rewriting_usepackage_with_options(self):
        self._do_test_with(r"\usepackage[length=3cm,width=2cm]{my-package}",
                           r"\usepackage[length=3cm,width=2cm]{my-package}")

        self._engine.relocate_package.assert_called_once_with("my-package", ANY)


    def test_rewriting_bibliography_style(self):
        self._engine.update_link_to_bibliography_style.return_value = "my-style"
        self._do_test_with(r"\bibliographystyle{my-style}",
                           r"\bibliographystyle{my-style}")

        self._engine.update_link_to_bibliography_style.assert_called_once_with("my-style", ANY)


if __name__ == '__main__':
    main()
