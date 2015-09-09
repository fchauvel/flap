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
from flap.engine import Flap, Listener, MissingGraphicFile
from flap.path import Path


class UI(Listener):
    """
    Gather all the interaction the console
    """
    
    def __init__(self, output=sys.stdout):
        self._output = output
        self.showDetails = False
    
    def enableDetails(self):
        self.showDetails = True
    
    def disableDetails(self):
        self.showDetails = False
    
    def onStartup(self):
        self.show("FLaP v" + flap.__version__ + " -- Flat LaTeX Projects")
        
    def on_input(self, fragment):
        self._show_fragment(fragment)
        
    def on_include_graphics(self, fragment):
        self._show_fragment(fragment)
        
    def on_include_SVG(self, fragment):
        self._show_fragment(fragment)
        
    def on_include(self, fragment):
        self._show_fragment(fragment)
        
    def on_flatten_complete(self):
        self.show("Flatten complete.")

    def on_missing_graphic(self, fragment):
        self.show("Error: Unable to find graphic file for %s" % fragment.text().strip())
        self.show("Check %s, line %d" % (fragment.file().fullname(), fragment.line_number()))

    def _show_fragment(self, fragment):
        if self.showDetails:
            text = "+ in '%s' line %d: '%s'" % (fragment.file().fullname(), fragment.line_number(), fragment.text().strip())
            self.show(text)

    def show(self, message):
        print(message, file=self._output)
        
    def show_usage(self):
        self.show("Usage: python -m flap <path/to/tex_file> <output/directory>")


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
        self.ui = factory.ui()
        self.flap = factory.flap()
        
    def run(self, arguments):
        if len(arguments) < 2 or len(arguments) > 3:
            self.ui.show_usage()
        else:
            (root_file, output, verbose) = self.parse(arguments)
            if verbose:
                self.ui.enableDetails()
            self.ui.onStartup()
            try:
                self.flap.flatten(root_file, output)

            except MissingGraphicFile as error:
                self.ui.on_missing_graphic(error.fragment())

    def parse(self, arguments):
        root_file = "main.tex"
        output = "/temp/"
        verbose = False
        for each in arguments:
            if each.endswith(".tex"):
                root_file = each
            elif each == "-v" or each == "--verbose":
                verbose = True
            else:
                output = each
        return Path.fromText(root_file), Path.fromText(output), verbose


def main(arguments):
    """
    Entry point of the FLaP utility.

    :param arguments: the command line arguments
    """
    Controller().run(arguments)


if __name__ == "__main__":
    main(sys.argv)  # For compatibility with versions prior to 0.2.3