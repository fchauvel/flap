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

from unittest import TestCase
from unittest.mock import MagicMock

from flap.engine import Flap
from flap.substitutions.factory import ProcessorFactory
from flap.ui import UI, Factory, Controller
from flap.util.oofs import InMemoryFileSystem
from flap.util.path import TEMP
from io import StringIO
from tests.latex_project import LatexProject, a_project, FlapTestCase


class TestRunner:

    def __init__(self, file_system, directory, ui=UI(StringIO())):
        self._file_system = file_system
        self._directory = directory
        self._ui = ui

    def test(self, name, project, expected):
        self._setup(name, project)
        self._move_to(name)
        self._run_flap(name)
        self._verify(name, expected)

    def _setup(self, name, project):
        project.setup(self._file_system, self._test_location(name))

    def _test_location(self, name):
        return self._directory / self._escape(name) / "project"

    @staticmethod
    def _escape(name):
        return name\
            .replace(" ", "_")\
            .replace("\\", "_")

    def _root_file(self, name):
        return self._test_location(name) / "main.tex"

    def _output_path(self, name):
        return self._directory / self._escape(name) / "flatten"

    def _destination(self, name):
        return self._output_path(name)

    def _run_flap(self, name):
        pass

    def _move_to(self, name):
        self._file_system.move_to_directory(self._test_location(name))

    def _verify(self, name, expected):
        output = self._file_system.open(self._output_path(name))
        actual = LatexProject.extract_from_directory(output)
        expected.assert_is_equivalent_to(actual)


class AcceptanceTestRunner(TestRunner):

    def __init__(self, file_system, directory, ui):
        super().__init__(file_system, directory, ui)

    def _run_flap(self, name):
        factory = Factory(self._file_system, self._ui)
        controller = Controller(factory)
        controller.run(self._arguments(name))

    def _arguments(self, name):
        return ["__main.py__", str(self._root_file(name)), str(self._destination(name))]


class UnitTestRunner(TestRunner):

    def __init__(self, file_system, directory, ui):
        super().__init__(file_system, directory, ui)

    def _run_flap(self, name):
        flap = Flap(self._file_system, ProcessorFactory(), listener=self._ui)
        flap.flatten(self._root_file(name), self._destination(name))

    def _destination(self, name):
        return self._output_path(name)


class FlapTest(TestCase):

    TEST_CASE_NAME = "unit_test"

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._ui = MagicMock()
        self._runner = UnitTestRunner(self._file_system, TEMP / "flap" , self._ui)
        self._assume = None
        self._expect = a_project()
        self._test_case = None

    def _do_test_and_verify(self):
        self._test_case = FlapTestCase(self.TEST_CASE_NAME, self._assume.build(), self._expect.build())
        self._test_case.run_with(self._runner)

    def _verify(self):
        self._test_case.verify(self._runner)

    def _verify_ui_reports_fragment(self, file_name, line_number, excerpt):
        fragment = self._ui.on_fragment.call_args[0][0]
        self.assertEqual(fragment.file().fullname(), file_name)
        self.assertEqual(fragment.line_number(), line_number)
        self.assertEqual(fragment.text().strip(), excerpt)


