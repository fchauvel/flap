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

import sys

import flap
from flap.engine import Flap, Listener, GraphicNotFound, TexFileNotFound
from flap.substitutions.factory import ProcessorFactory
from flap.util.oofs import OSFileSystem
from flap.util.path import Path, TEMP


class UI(Listener):
    """
    Gather all the interaction the console
    """

    def __init__(self, output=sys.stdout, is_verbose=False):
        self._output = output
        self._verbose = is_verbose

    def set_verbose(self, is_activated):
        self._verbose = is_activated
    
    def show_opening_message(self):
        self._show("FLaP v" + flap.__version__ + " -- Flat LaTeX Projects")

    def on_fragment(self, fragment):
        self.show_fragment(fragment)

    def show_closing_message(self):
        self._show("Flatten complete.")

    def report_missing_graphic(self, fragment):
        self._show("Error: Unable to find graphic file for %s" % fragment.text().strip())
        self._show("Check %s, line %d" % (fragment.file().fullname(), fragment.line_number()))

    def report_missing_tex_file(self, fragment):
        self._show("Error: Unable to find LaTeX file referred in '%s'" % fragment.text().strip())
        self._show("Check %s, line %d" % (fragment.file().fullname(), fragment.line_number()))

    def report_unexpected_error(self, message):
        self._show("Error: %s" % message)

    def show_fragment(self, fragment):
        if self._verbose:
            text = "+ in '%s' line %d: '%s'" % (fragment.file().fullname(), fragment.line_number(), fragment.text().strip())
            self._show(text)

    def _show(self, message):
        print(message, file=self._output)
        
    def show_usage(self):
        self._show("Usage: python -m flap <path/to/tex_file> <output/directory>")


class Factory:
    """
    Encapsulate the construction of FLaP, UI and FileSystem objects
    """

    def __init__(self, file_system = OSFileSystem(), ui=UI()):
        self._file_system = file_system
        self._ui = ui
        self._flap = Flap(self._file_system, ProcessorFactory(), self._ui)

    def ui(self):
        return self._ui

    def flap(self):
        return self._flap


class Controller:
    """
    Controller, as in the Model-View-Controller pattern. Receive commands, and
    update the view accordingly.
    """
    
    def __init__(self, factory=Factory()):
        self._ui = factory.ui()
        self._flap = factory.flap()
        self._root_file = "main.tex"
        self._output = TEMP / "flap"
        self._verbose = False

    def run(self, arguments):
        try:
            self.parse(arguments)
            self._ui.set_verbose(self._verbose)
            self._ui.show_opening_message()
            self._flap.flatten(self._root_file, self._output)
            self._ui.show_closing_message()

        except IllegalArguments:
            self._ui.show_usage()

        except GraphicNotFound as error:
            self._ui.report_missing_graphic(error.fragment())

        except TexFileNotFound as error:
            self._ui.report_missing_tex_file(error.fragment())

        except Exception as error:
            self._ui.report_unexpected_error(str(error))

    def parse(self, arguments):
        if len(arguments) < 3 or len(arguments) > 4:
            raise IllegalArguments("Wrong number of arguments (found %s)" % str(arguments))

        root_set = False
        for any_argument in arguments:
            if any_argument == "__main__.py": continue
            if any_argument in ["-v", "--verbose"]:
                self._verbose = True
            elif any_argument.endswith(".tex"):
                if not root_set:
                    self._root_file = Path.fromText(any_argument)
                    root_set = True
                else:
                    self._output = Path.fromText(any_argument)
            else:
                self._output = Path.fromText(any_argument)


class IllegalArguments(ValueError):
    """
    Raised when FLaP cannot parse the the arguments received from the command line
    """
    pass


def main(arguments):
    Controller().run(arguments)

if __name__ == "__main__":
    main(sys.argv)  # For compatibility with versions prior to 0.2.3
