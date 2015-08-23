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
import os
import subprocess
from setuptools import Command

import flap


class Version:
    
    @staticmethod
    def fromText(text):
        pattern = re.compile("(\\d+)\\.(\\d+)(?:\\.(?:dev)?(\\d+))?")
        match = re.match(pattern, text)
        return Version(int(match.group(1)), int(match.group(2)), int(match.group(3)) if match.group(3) else None)
                    
    def __init__(self, major, minor, micro=None):
        self.major = major
        self.minor = minor
        self.micro = micro
        
    def hasMinor(self, minor):
        return self.minor == minor
    
    def hasMajor(self, major):
        return self.major == major
        
    def hasMicro(self, micro):
        return self.micro == micro
    
    def nextMicroRelease(self):
        return Version(self.major, self.minor, self.micro + 1)
            
    def nextMinorRelease(self):
        return Version(self.major, self.minor + 1, 0)
            
    def nextMajorRelease(self):
        return Version(self.major + 1, 0, 0)            
            
    def __repr__(self):
        version = "{}.{}".format(self.major, self.minor)
        if self.micro is not None:
            version += ".%d" % self.micro
        return version
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return (other and isinstance(other, Version) and
                other.micro == self.micro and
                other.hasMajor(self.major) and
                other.hasMinor(self.minor))

class Sources:
    
    LOCATION = "flap/__init__.py"
    
    def readVersion(self):
        return Version.fromText(flap.__version__)
    
    def writeVersion(self, version):
        content = open(Sources.LOCATION).read()
        content = content.replace(flap.__version__, str(version))
        updated = open(Sources.LOCATION, "w")
        updated.write(content)
        updated.flush()
        updated.close()


class SourceControl:
    
    def __init__(self):
        self.environment = os.environ.copy()
        self.environment["PATH"] += """C:\Program Files (x86)\Git\\bin\;"""

    
    def commit(self, message):
        command = ["git", "commit", "-m", "\"%s\"" % message ]
        subprocess.call(command, env=self.environment, shell=True)
    
    def tag(self, version):
        command = ["git", "tag", "-a", "v" + str(version), "-m", "\"Version %s\"" % str(version) ]
        subprocess.call(command, env=self.environment, shell=True)
        command = ["git", "push", "--tag"]
        subprocess.call(command, env=self.environment, shell=True)
    
    
class Release(Command):
            
    def __init__(self, dist, scm = SourceControl(), sources = Sources()):
        super().__init__(dist)
        self.scm = scm
        self.sources = sources
            
    user_options = [('next=', None, 'The type of release (micro, minor or major')]
    
    def initialize_options(self):
        self.next = ""
        
    def finalize_options(self):
        pass
    

    def run(self):      
        version = self.sources.readVersion()
        print("Releasing version: %s" % version)
        self.scm.commit("Releasing version %s" % version)
        self.scm.tag(version)
        newVersion = self.nextVersion(version)
        self.sources.writeVersion(newVersion)
        print("Preparing for version: " + str(newVersion))
        self.scm.commit("Preparing version %s" % newVersion)
                
    def nextVersion(self, version):
        if self.next == "micro":
            return version.nextMicroRelease()
        elif self.next == "minor":
            return version.nextMinorRelease()
        elif self.next == "major":
            return version.nextMajorRelease()
        else:
            raise ValueError("Unknown type of release '%s' (options are %s)." % (self.next, ["micro", "minor", "major"]))
