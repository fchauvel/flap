#!/usr/bin/env python

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

import flap
import re
import subprocess
from setuptools import setup, find_packages, Command

class Version:
    
    def __init__(self, versionText):
        pattern = re.compile("(\\d+)\\.(\\d+)(?:\\.(\\w+))?")
        match = re.match(pattern, versionText)
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.kind = match.group(3)
        
    def isUnderDevelopment(self):
        return self.kind is not None
    
    def finalize(self):
        if self.isUnderDevelopment():
            self.kind = None
            self.updateSources()
            
    def initialize(self):
        self.kind = "dev"
            
    def minorIncrement(self):
        self.minor = self.minor + 1
        self.updateSources()
        
    def majorIncrement(self):
        self.major = self.major + 1
        self.updateSources()
        
    def __repr__(self):
        version = "{}.{}".format(self.major, self.minor)
        if self.isUnderDevelopment():
            version += ".dev"
        return version
    
    def updateSources(self):
        content = open("flap/__init__.py").read()
        content = content.replace(flap.__version__, self.__repr__())
        updated = open("flap/__init__.py", "w")
        updated.write(content)
        updated.flush()
        updated.close()
        
    def execute(self, arguments):
        subprocess.call(arguments)
    
class Release(Command):
            
    user_options = []
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
    
    def run(self):
        self.version = Version(flap.__version__)
        self.finalize() 
#         self.commit()
#         self.tag()
#         self.build()
#         self.publish()
#         self.increment()
        
    def finalize(self):
        print("Finalizing v%s"  % self.version)
        self.version.finalize()
        
    def commit(self):
        print("git commit -m \"Releasing v%s\"" % self.version)
        print("git push")
        
    def tag(self):
        print("git tag -a v{0} -m \"Release {0}\"".format(self.version))
        print("git push --tag")
        
    def build(self):
        print("python setup.py sdist")
        
    def publish(self):
        print("Uploading distribution to GitHub")

    def increment(self):
        self.version.minorIncrement()
        self.version.initialize()
        print("Preparing development of v%s" % self.version)

setup(name='FLaP',
     version=flap.__version__,
     description='Flat LaTeX Projects', 
     author='Franck Chauvel',
     author_email='franck.chauvel@gmail.com',
     license="GPLv3",
     url='https://github.com/fchauvel/flap',
     download_url="https://github.com/fchauvel/flap/releases",
     packages=find_packages(exclude='tests'),
     test_suite = "tests",
     cmdclass = { "release": Release}
     )



