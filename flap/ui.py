
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
        
    def onInput(self, inputedFile):
        self.show(" - input: " + inputedFile)
        
    def onFlattenComplete(self):
        self.show("Flatten complete.")
        
    def show(self, message):
        print(message, file=self.output)
        
        

class Command:
    """
    An invocation of the FLaP tool
    """
        
    @staticmethod
    def parse(arguments):
        command = Command() 
        for each in arguments:
            if each.endswith(".tex"):
                command.setRootFile(each)
            else:
                command.setOutputDirectory(each)
        return command
                
    
    def __init__(self):
        self._outputDirectory = tempfile.gettempdir()
        self._rootFile = "main.tex"
        
    def outputDirectory(self):
        return self._outputDirectory
    
    def setOutputDirectory(self, outputDirectory):
        self._outputDirectory = outputDirectory
    
    def rootFile(self):
        return self._rootFile
    
    def setRootFile(self, rootFile):
        self._rootFile = rootFile
        
    def sendTo(self, flap):
        flap.flatten(Path.fromText(self.rootFile()), Path.fromText(self.outputDirectory()))
        

class Controller:
    """
    Controller, as in the Model-View-Controller pattern. Receive command, and 
    update the view accordingly 
    """
    
    def __init__(self, fileSystem, ui=UI()):
        self.ui = ui
        self.engine = Flap(fileSystem, self.ui)
        
    def run(self, arguments):
        command = Command.parse(arguments)
        command.sendTo(self.engine)
        
        
if __name__ == "__main__":
    Controller(OSFileSystem()).run(sys.argv)