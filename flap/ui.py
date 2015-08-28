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
from flap.core import Flap, Listener
from flap.path import Path


class UI(Listener):
    """
    Gather all the interaction the console
    """
    
    def __init__(self, output=sys.stdout):
        self.output = output
        self.showDetails = False
    
    def enableDetails(self):
        self.showDetails = True
    
    def disableDetails(self):
        self.showDetails = False
    
    def onStartup(self):
        self.show("FLaP v" + flap.__version__ + " -- Flat LaTeX Projects")
        
    def on_input(self, fragment):
        self.showFragment(fragment)
        
    def on_include_graphics(self, fragment):
        self.showFragment(fragment)
        
    def on_include_SVG(self, fragment):
        self.showFragment(fragment)
        
    def on_include(self, fragment):
        self.showFragment(fragment)
        
    def on_flatten_complete(self):
        self.show("Flatten complete.")
        
    def showFragment(self, fragment):
        if self.showDetails:
            text = "+ in '%s' line %d: '%s'" % (fragment.file().fullname(), fragment.line_number(), fragment.text().strip())
            self.show(text)

    def show(self, message):
        print(message, file=self.output)
        

class Controller:
    """
    Controller, as in the Model-View-Controller pattern. Receive command, and 
    update the view accordingly 
    """
    
    def __init__(self, fileSystem, ui=UI()):
        self.ui = ui
        self.flap = Flap(fileSystem, ui)
        
    def run(self, arguments):
        (rootFile, output, isVerbose) = self.parse(arguments)
        if isVerbose:
            self.ui.enableDetails()
        self.ui.onStartup()
        self.flap.flatten(rootFile, output)
        
    def parse(self, arguments):
        rootFile = "main.tex"
        output = "/temp/"
        verbose = False
        for each in arguments:
            if each.endswith(".tex"):
                rootFile = each
            elif each == "-v" or each == "--verbose":
                verbose = True
            else:
                output = each
        return Path.fromText(rootFile), Path.fromText(output), verbose


def main(arguments):
    """
    Entry point of the FLaP utility.

    :param arguments: the command line arguments
    """
    Controller(OSFileSystem()).run(arguments)


if __name__ == "__main__":
    print("Pouet!")