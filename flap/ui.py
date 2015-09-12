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
from flap.FileSystem import OSFileSystem
from flap.engine import Flap, Listener, GraphicNotFound, TexFileNotFound
from flap.path import Path


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
        
    def on_input(self, fragment):
        self._show_fragment(fragment)
        
    def on_include_graphics(self, fragment):
        self._show_fragment(fragment)
        
    def on_include_SVG(self, fragment):
        self._show_fragment(fragment)
        
    def on_include(self, fragment):
        self._show_fragment(fragment)
        
    def show_closing_message(self):
        self._show("Flatten complete.")

    def report_missing_graphic(self, fragment):
        self._show("Error: Unable to find graphic file for %s" % fragment.text().strip())
        self._show("Check %s, line %d" % (fragment.file().fullname(), fragment.line_number()))

    def report_missing_tex_file(self, fragment):
        self._show("Error: Unable to find LaTeX file '%s'" % fragment.text().strip())
        self._show("Check %s, line %d" % (fragment.file().fullname(), fragment.line_number()))

    def report_unexpected_error(self, message):
        self._show("Error: %s" % message)

    def _show_fragment(self, fragment):
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
        self._flap = Flap(self._file_system, self._ui)

    def ui(self):
        return self._ui

    def flap(self):
        return self._flap


class Controller:
    """
    Controller, as in the Model-View-Controller pattern. Receive command, and 
    update the view accordingly 
    """
    
    def __init__(self, factory=Factory()):
        self._ui = factory.ui()
        self._flap = factory.flap()
        
    def run(self, arguments):
        if len(arguments) < 3 or len(arguments) > 4:
            self._ui.show_usage()
        else:
            (root_file, output, verbose) = self.parse(arguments)
            self._ui.set_verbose(verbose)
            self._ui.show_opening_message()
            try:
                self._flap.flatten(root_file, output)
                self._ui.show_closing_message()

            except GraphicNotFound as error:
                self._ui.report_missing_graphic(error.fragment())
            except TexFileNotFound as error:
                self._ui.report_missing_tex_file(error.fragment())
            except Exception as error:
                self._ui.report_unexpected_error(str(error))



    def parse(self, arguments):
        root_file = "main.tex"
        output = "/temp/"
        verbose = False
        for any_argument in arguments:
            if any_argument.endswith(".tex"):
                root_file = any_argument
            elif any_argument == "-v" or any_argument == "--verbose":
                verbose = True
            else:
                output = any_argument
        return Path.fromText(root_file), Path.fromText(output), verbose


def main(arguments):
    Controller().run(arguments)


if __name__ == "__main__":
    main(sys.argv)  # For compatibility with versions prior to 0.2.3