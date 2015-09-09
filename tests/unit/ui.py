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
from unittest import TestCase, main
from mock import patch, MagicMock
import flap
from io import StringIO
from flap.path import ROOT, TEMP
from flap.engine import Fragment, Flap, MissingGraphicFile
from flap.FileSystem import File
from flap.ui import UI, Controller, Factory


class UiTest(TestCase):
    
    def makeUI(self, mock):
        ui = UI(mock)
        ui.enableDetails()
        return ui
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_displays_version_number(self, mock):
        ui = self.makeUI(mock)        
        ui.onStartup()
        self.verify_output_contains(mock, flap.__version__)

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_input(self, mock):
        ui = self.makeUI(mock)     
        self.run_test(ui.on_input, mock, ["main.tex", "3", "foo"])
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_includesvg(self, mock):
        ui = self.makeUI(mock)
        self.run_test(ui.on_include_SVG, mock, ["main.tex", "3", "foo"])

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_include(self, mock):
        ui = self.makeUI(mock)        
        self.run_test(ui.on_include, mock,["main.tex", "3", "foo"])
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_includegraphics(self, mock):
        ui = self.makeUI(mock)
        self.run_test(ui.on_include_graphics, mock, ["main.tex", "3", "foo"])

    @patch("sys.stdout", new_callable=StringIO)
    def test_ui_reports_missing_image(self, mock):
        ui = self.makeUI(mock)
        self.run_test(ui.on_missing_graphic, mock,["main.tex", "3", "foo"])

    @patch('sys.stdout', new_callable=StringIO)
    def test_ui_reports_completion(self, mock):
        ui = self.makeUI(mock)

        ui.on_flatten_complete()

        self.verify_output_contains(mock, "complete")

    def run_test(self, operation, mock, expectedOutputs):
        operation(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))
        for eachOutput in expectedOutputs:
            self.verify_output_contains(mock, eachOutput)

    @patch('sys.stdout', new_callable=StringIO)
    def test_disabling_reporting(self, mock):
        ui = self.makeUI(mock)
        ui.disableDetails()

        ui.on_include_graphics(Fragment(File(None, ROOT/"main.tex", None), 3, "foo"))

        self.assertFalse(mock.getvalue())

    def verify_output_contains(self, mock, pattern):
        output = mock.getvalue()
        self.assertIsNotNone(re.search(pattern, output), output)


class ControllerTest(TestCase):
    """
    Specify the behaviour of the controller
    """

    def test_missing_images_are_reported_to_the_ui(self):
        flap_mock = MagicMock(Flap)
        fragment = MagicMock(Fragment)
        flap_mock.flatten.side_effect = MissingGraphicFile(fragment, "img/foo")

        ui_mock = MagicMock(UI)
        factory = MagicMock(Factory)
        factory.ui.return_value = ui_mock
        factory.flap.return_value = flap_mock

        controller = Controller(factory)

        controller.run(["foo", "bar"])

        ui_mock.on_missing_graphic.assert_called_once_with(fragment)

if __name__ == "__main__":
    main()