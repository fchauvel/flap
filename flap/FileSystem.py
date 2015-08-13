
import os
import re

from flap.path import Path

class File:
   
    def __init__(self, fileSystem, path, content):
        assert path, "Invalid path (found '%s')" % path.full()
        self.fileSystem = fileSystem
        self._path = path
        self._content = content
    
    def isFile(self):
        return True
    
    def isDirectory(self):
        return not self.isFile()
    
    def exists(self):
        return True
    
    def isMissing(self):
        return not self.exists()
    
    def contains(self, content):
        return self._content == content
    
    def content(self):
        if not self._content:
            self._content = self.fileSystem.load(self._path)
        return self._content

    def path(self):
        return self._path
    
    def fullname(self):
        return self._path.fullname()
    
    def basename(self):
        return self._path.basename()
    
    def hasExtension(self):
        return self._path.hasExtension()
    
    def extension(self):
        return self._path.extension()
    
    def container(self):
        return self.fileSystem.open(self._path.container())
        
    def sibling(self, name):
        return self.fileSystem.open(self._path.container() / name) 
    
    def files(self):
        return []
    
    def filesThatMatches(self, pattern):
        path = Path.fromText(str(self._path) + "/" + str(pattern)) 
        dir = self.fileSystem.open(path.container())
        return [ file for file in dir.files() if re.search(path.fullname(), str(file.path())) ]
    
    def __repr__(self):
        return self.path()
    
    
class Directory(File):
    
    def __init__(self, fileSystem, path):
        super().__init__(fileSystem, path, None)
             
    def isFile(self):
        return False
    
    def content(self):
        return None 
            
    def files(self):
        return self.fileSystem.filesIn(self.path())
     
    
class MissingFile(File):
    
    def __init__(self, path):
        super().__init__(None, path, None)
        
    def exists(self):
        return False
    
    def contains(self, content):
        return False
    
    def content(self):
        return None
    
    def location(self):
        return None


class FileSystem:
    
    def createFile(self, path, content):
        pass
    
    def createDirectory(self, path):
        pass
    
    def open(self, path):
        pass
    
    def filesIn(self, path):
        pass
    
    def copy(self, file, destination):
        pass
    
    def load(self, path):
        pass
    
   



class OSFileSystem(FileSystem):
    
    def __init__(self):
        super().__init__()
        
    def forOS(self, path):
        return "\\".join(path.parts())
            
        
    def createFile(self, path, content):
        osDirPath = self.forOS(path.container())
        if not os.path.exists(osDirPath):
            os.makedirs(osDirPath)
        osPath = self.forOS(path) 
        with open(osPath, "w") as f:
            f.write(content)
        
    def deleteDirectory(self, path):
        import shutil
        osPath = self.forOS(path)
        if os.path.exists(osPath):
            shutil.rmtree(osPath)
    
    def open(self, path):
        osPath = self.forOS(path)
        if os.path.isdir(osPath):
            return Directory(self, path)
        else:
            return File(self, path, None)

    def filesIn(self, path):
        return [ self.open(path / each) for each in os.listdir(self.forOS(path)) ]         
    
    
    def copy(self, file, destination):
        import shutil
        targetDir = self.forOS(destination)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir) 
        source = self.forOS(file.path())
        target = self.forOS(destination / file.fullname())
        shutil.copyfile(source, target)
        

    def load(self, path):
        assert path, "Invalid path (found '%s')" % path
        osPath = self.forOS(path)
        with open(osPath) as file:
            return file.read()
    


class InMemoryFileSystem(FileSystem):
        
    def __init__(self, pathSeparator = os.path.sep):
        super().__init__()
        self.drive = {}
        self.pathSeparator = pathSeparator 

    
    def createDirectory(self, path):
        if path in self.drive.keys():
            if self.drive[path].isFile():
                raise ValueError("There is already a resource at '%s'" % path.full())
        self.drive[path] = Directory(self, path)
        if not path.isRoot():
            self.createDirectory(path.container())
        
    
    def createFile(self, path, content):
        self.drive[path] = File(self, path, content)
        self.createDirectory(path.container())
        
    def filesIn(self, path):
        return [ self.drive[p] for p in self.drive.keys() if p in path ]
        
    def open(self, path):
        if path in self.drive.keys():
            return self.drive[path]
        else:
            return MissingFile(path)
        
    def copy(self, file, destination):
        path = destination / file.path().fullname()
        self.drive[path] = File(self, path, file.content())
        