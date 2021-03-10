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

from io import StringIO

from flap import __version__
from flap.util import truncate
from flap.util.path import Path, TEMP
from flap.ui import Display, Controller
from tests.latex_project import LatexProject


class EndToEndRunner:

    def __init__(self, file_system):
        self._file_system = file_system

    def test(self, test_case):
        self._tear_down(test_case)
        self._setup(test_case)
        self._execute(test_case)
        self._verify(test_case)

    def _tear_down(self, test_case):
        self._output = StringIO()
        self._display = Display(self._output, verbose=True)
        self._controller = Controller(self._file_system, self._display)
        self._file_system.deleteDirectory(self._path_for(test_case))

    def _setup(self, test_case):
        test_case._project.setup(
            self._file_system,
            self._path_for(test_case) /
            "project")

    @staticmethod
    def _path_for(test_case):
        return TEMP / "flap" / "acceptance" / test_case.escaped_name

    def _execute(self, test_case):
        self._file_system.move_to_directory(self._path_for(test_case))
        self._controller.run(tex_file="./project/" +
                             test_case._invocation.tex_file, output="output")

    def _verify(self, test_case):
        self._verify_generated_files(test_case)
        self._verify_console_output(test_case)

    def _verify_generated_files(self, test_case):
        location = self._file_system.open(Path.fromText("output"))
        actual = LatexProject.extract_from_directory(location)
        test_case._expected.assert_is_equivalent_to(actual)

    def _verify_console_output(self, test_case):
        self._verify_shown(__version__)
        self._verify_shown(self._display.HEADER)
        self._verify_shown(self._display._horizontal_line())
        entries = [each.as_dictionary for each in test_case._output]
        for each_entry in entries:
            each_entry["code"] = truncate(
                each_entry["code"], self._display.WIDTHS[3])
            self._verify_shown(self._display.ENTRY.format(**each_entry))
        self._verify_shown(
            self._display.SUMMARY.format(
                count=len(
                    test_case._output)))

    def _verify_shown(self, text):
        message = "Could not find the following text:\n" \
                  "  \"{pattern}\"\n" \
                  "\n" \
                  "The output was:\n" \
                  "{output}\n"
        if text not in self._output.getvalue():
            raise AssertionError(
                message.format(
                    pattern=text,
                    output=self._output.getvalue()))
