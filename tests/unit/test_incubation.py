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

from io import StringIO
from flap import __version__
from flap.incubation import Controller, Display
from flap.util.oofs import InMemoryFileSystem
from flap.util.path import Path
from tests.latex_project import a_project, LatexProject


class EndToEndTest(TestCase):

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._assume = None
        self._test_case = None
        self._output = StringIO()
        self._display = Display(self._output)
        self._controller = Controller(self._file_system, self._display)

    def assume(self, project):
        self._assume = project

    def invoke_flap(self):
        assert self._assume, "No project defined!"
        latex_project = self._assume.build()
        latex_project.setup(self._file_system, Path.fromText("tests"))
        self._controller.run(["__main.py__", "tests/main.tex", "output"])

    def verify_generated(self, expected):
        location = self._file_system.open(Path.fromText("output"))
        actual = LatexProject.extract_from_directory(location)
        actual.assert_is_equivalent_to(expected.build())

    def verify_output(self, entries):
        self._verify_shown(__version__)
        self._verify_shown(self._display.HEADER)
        self._verify_shown(self._display._horizontal_line())
        for each_entry in entries:
            self._verify_shown(self._display.ENTRY.format(**each_entry))
        self._verify_shown(self._display.SUMMARY.format(count=len(entries)))

    def _verify_shown(self, text):
        self.assertIn(text, self._output.getvalue())


class ControllerTests(EndToEndTest):

    def test_flatten_a_file_without_known_commands(self):
        self.assume(
            a_project().with_main_file("Blabla")
        )

        self.invoke_flap()

        self.verify_generated(
            a_project().with_merged_file("Blabla")
        )

        self.verify_output(entries=[])

    def test_flatten_a_simple_file(self):
        self.assume(
            a_project()\
                .with_main_file("Blabla \n"
                                "\\input{result.tex} \n"
                                "Blabla \n")\
                .with_file("result.tex", "Some results"))

        self.invoke_flap()

        self.verify_generated(
            a_project().with_merged_file("Blabla \n"
                                         "Some results \n"
                                         "Blabla \n"))

        self.verify_output([
            {"file": "test.tex", "line": 2, "column": 1, "code": r"\input{result.tex}"}
        ])

        print(self._output.getvalue())

    def test_flatten_an_include_graphics(self):
        self.assume(
            a_project()
                .with_main_file("Blabla \n"
                                "\includegraphics{img/result.pdf}\n"
                                "Blabla \n")\
                .with_image("img/result.pdf"))

        self.invoke_flap()

        self.verify_generated(
            a_project()
                .with_merged_file("Blabla \n"
                                  "\includegraphics{img_result}\n"
                                  "Blabla \n")
                .with_image("img_result.pdf"))

        self.verify_output([
            {"file": "test.tex", "line": 2, "column": 1, "code": r"\includegraphics{img/result.pdf}"}
        ])

        print(self._output.getvalue())


if __name__ == "__main__":
    main()

