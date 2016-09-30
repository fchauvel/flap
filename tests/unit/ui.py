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

import flap
import re
from flap.engine import Fragment, Flap, GraphicNotFound, TexFileNotFound
from flap.ui import UI, Controller, Factory
from flap.util.oofs import File
from flap.util.path import ROOT, Path
from io import StringIO
from mock import patch, MagicMock


class UiTest(TestCase):
    
    def makeUI(self, mock):
        ui = UI(mock, True)
        return ui
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_displays_version_number(self, mock):
        ui = self.makeUI(mock)        
        ui.show_opening_message()
        self.verify_output_contains(mock, flap.__version__)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_fragment(self, mock):
        ui = self.makeUI(mock)     
        self.run_test(ui.on_fragment, mock, ["main.tex", "3", "foo"])

    @patch("sys.stdout", new_callable=StringIO)
    def test_ui_reports_missing_image(self, mock):
        ui = self.makeUI(mock)
        self.run_test(ui.report_missing_graphic, mock,["main.tex", "3", "foo"])

    @patch("sys.stdout", new_callable=StringIO)
    def test_ui_reports_missing_tex_file(self, mock):
        ui = self.makeUI(mock)
        self.run_test(ui.report_missing_tex_file, mock,["main.tex", "3", "foo"])

    @patch("sys.stdout", new_callable=StringIO)
    def test_ui_reports_unexpected_error(self, mock):
        ui = self.makeUI(mock)
        ui.report_unexpected_error("foo")
        self.verify_output_contains(mock, "foo")

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_completion(self, mock):
        ui = self.makeUI(mock)

        ui.show_closing_message()

        self.verify_output_contains(mock, "complete")

    def run_test(self, operation, mock, expected_outputs):
        operation(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))
        for each_output in expected_outputs:
            self.verify_output_contains(mock, each_output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_disabling_reporting(self, mock):
        ui = self.makeUI(mock)
        ui.set_verbose(False)

        ui.on_fragment(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.assertFalse(mock.getvalue())

    def verify_output_contains(self, mock, pattern):
        output = mock.getvalue()
        self.assertIsNotNone(re.search(pattern, output), output)


class ControllerTest(TestCase):

    def setUp(self):
        self.flap_mock = MagicMock(Flap)
        self.ui_mock = MagicMock(UI)
        factory = MagicMock(Factory)
        factory.ui.return_value = self.ui_mock
        factory.flap.return_value = self.flap_mock
        self.controller = Controller(factory)

    def set_flap_behaviour(self, exception):
        self.flap_mock.flatten.side_effect = exception

    def test_missing_images_are_reported_to_the_ui(self):
        fragment = MagicMock(Fragment)
        self.set_flap_behaviour(GraphicNotFound(fragment))

        self._run_flap(["__main__.py", "foo", "bar"])

        self.ui_mock.report_missing_graphic.assert_called_once_with(fragment)

    def test_missing_tex_file_are_reported_to_the_ui(self):
        fragment = MagicMock(Fragment)
        self.set_flap_behaviour(TexFileNotFound(fragment))

        self._run_flap(["__main__.py", "foo", "bar"])

        self.ui_mock.report_missing_tex_file.assert_called_once_with(fragment)

    def test_unexpected_error_are_reported_to_the_ui(self):
        self.set_flap_behaviour(ValueError("foo"))

        self._run_flap(["__main__.py", "foo", "bar"])

        self.ui_mock.report_unexpected_error.assert_called_once_with("foo")

    def test_completion_is_reported(self):
        self._run_flap(["__main__.py", "foo", "bar"])

        self.ui_mock.show_closing_message.assert_called_with()

    def test_running_flap_with_a_specific_output_dir(self):
        self._run_flap(["__main__.py", "foo.tex", "output"])
        self.flap_mock.flatten.assert_called_once_with(Path.fromText("foo.tex"), Path.fromText("output"))

    def test_running_flap_with_a_specific_output_file(self):
        self._run_flap(["__main__.py", "foo.tex", "output/root.tex"])
        self.flap_mock.flatten.assert_called_once_with(Path.fromText("foo.tex"), Path.fromText("output/root.tex"))

    def _run_flap(self, parameters):
        self.controller.run(parameters)


if __name__ == "__main__":
    main()