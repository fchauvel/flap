
import sys
import tempfile
from flatexer.core import Flatexer
from flatexer.path import Path
from flatexer.FileSystem import OSFileSystem


class Command:
    
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
        
    def sendTo(self, flatexer):
        flatexer.flatten(Path.fromText(self.rootFile()), Path.fromText(self.outputDirectory()))
        

class Runner:
    
    def __init__(self, fileSystem):
        self.engine = Flatexer(fileSystem)
        
    def run(self, arguments):
        command = Command.parse(arguments)
        command.sendTo(self.engine)
        
        
if __name__ == "__main__":
    Runner(OSFileSystem()).run(sys.argv)