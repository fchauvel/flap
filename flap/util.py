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
from setuptools.command.bdist_egg import bdist_egg
import flap


class Version:

    LOCATION = "flap/__init__.py"

    @staticmethod
    def from_source_code():
        return Version.fromText(flap.__version__)

    @staticmethod
    def update_source_code(version):
        content = open(Version.LOCATION).read()
        replacement = "__version__ = \"%s\"" % str(version)
        new_content = re.sub(r"__version__\s*=\s*\"\d+\.\d+\.\d+\"", replacement, content)
        with open(Version.LOCATION, "w") as updated:
            updated.write(new_content)
            updated.flush()

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


class SourceControl:
    
    def __init__(self):
        self.environment = os.environ.copy()
        self.environment["PATH"] += ";C:/Program Files (x86)/Git/bin/"

    def commit(self, message):
        command = ["git.exe", "add", "-u"]
        subprocess.call(command, env=self.environment, shell=True)
        command = ["git.exe", "commit", "-m", "%s" % message ]
        subprocess.call(command, env=self.environment, shell=True)
    
    def tag(self, version):
        command = ["git.exe", "tag", "-a", "v" + str(version), "-m", "\"Version %s\"" % str(version) ]
        subprocess.call(command, env=self.environment, shell=True)
    
    
class Release(Command):
            
    def __init__(self, dist, scm = SourceControl()):
        super().__init__(dist)
        self.scm = scm

    user_options = [('type=', None, 'The type of release (micro, minor or major')]
    
    def initialize_options(self):
        self.type = ""
        
    def finalize_options(self):
        pass
    
    def run(self):      
        current_version = self.release()
        self.prepare_next_release(current_version)

    def release(self):
        current_version = Version.from_source_code()
        print("Current version: %s" % current_version)

        released_version = self.released_version(current_version)
        print("Releasing version %s" % released_version)
        if current_version != released_version:
            Version.update_source_code(released_version)
            self.distribution.version = str(released_version)
            self.distribution.metadata.version = str(released_version)
            self.scm.commit("Releasing version %s" % released_version)

        self.scm.tag(released_version)
        self.build()
        self.publish()
        return released_version

    def released_version(self, current_version):
        if self.type == "micro":
            return current_version
        elif self.type == "minor":
            return current_version.nextMinorRelease()
        elif self.type == "major":
            return current_version.nextMajorRelease()
        else:
            raise ValueError("Unknown release kind '%s' (options are 'micro', 'minor' or 'major')" % self.type)

    def build(self):
        self.run_command("bdist_egg")
        self.run_command("sdist")

    def publish(self):
        self.run_command("register")
        self.run_command("upload")

    def prepare_next_release(self, current_version):
        new_version = current_version.nextMicroRelease()
        Version.update_source_code(new_version)
        print("Preparing version " + str(new_version))
        self.scm.commit("Preparing version %s" % new_version)
        
