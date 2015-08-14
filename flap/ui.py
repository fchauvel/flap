

import sys
import tempfile

from flap.core import Flap, Listener
from flap.path import Path
from flap.FileSystem import OSFileSystem


class UI(Listener):
    """
    Gather all the interaction the console
    """
    
    def __init__(self, output=sys.stdout):
        self.output = output
    
    def onStartup(self):
        self.show("FLaP v0.1")
        
    def onInput(self, fragment):
        self.showFragment(fragment)
        
    def onIncludeGraphics(self, fragment):
        self.showFragment(fragment)
        
    def onFlattenComplete(self):
        self.show("Flatten complete.")
        
    def showFragment(self, fragment):
        text = "+ in '%s' line %d: '%s'" % (fragment.file().fullname(), fragment.lineNumber(), fragment.text())
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
        self.ui.onStartup()
        (rootFile, output) = self.parse(arguments)
        self.flap.flatten(rootFile, output)
        
    def parse(self, arguments):
        rootFile = "main.tex"
        output = "/temp/"
        for each in arguments:
            if each.endswith(".tex"):
                rootFile = each
            else:
                output = each
        return (Path.fromText(rootFile), Path.fromText(output))
        
if __name__ == "__main__":
    Controller(OSFileSystem()).run(sys.argv)