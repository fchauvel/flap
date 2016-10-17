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


class ControllerTests(TestCase):

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._output = StringIO()
        self._display = Display(self._output)
        self._controller = Controller(self._file_system, self._display)

    def test_show_version(self):
        self._controller.run([])
        self.assertIn(__version__, self._output.getvalue())

    def test_flatten_a_dummy_file(self):
        self._file_system.create_file(Path.fromText("test.tex"),
                                      "Blabla \n"
                                      "\\input{result.tex} \n"
                                      "Blabla \n")
        self._file_system.create_file(Path.fromText("result.tex"),
                                      "Some results")

        self._controller.run(["__main.py__", "test.tex", "output"])

        flattened_file = self._file_system.open(Path.fromText("output/merged.tex"))
        self.assertIsNotNone(flattened_file)
        self.assertEqual("Blabla \n"
                         "Some results \n"
                         "Blabla \n",
                         flattened_file.content()
                         )

        self.assertIn(__version__, self._output.getvalue())
        self.assertIn(self._display.HEADER, self._output.getvalue())
        self.assertIn(self._display._horizontal_line(), self._output.getvalue())
        self.assertIn(self._display.ENTRY.format(file="test.tex", line=2, column=1, code="\\input{result.tex}"), self._output.getvalue())

        print(self._output.getvalue())

if __name__ == "__main__":
    main()

