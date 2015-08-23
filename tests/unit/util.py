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

from unittest import TestCase, main
from unittest.mock import MagicMock, call

from flap.util import Version, Release, SourceControl, Sources 
from distutils.dist import Distribution

class VersionTest(TestCase):

    
    def makeVersion(self, text):
        return Version.fromText(text)

    def verifyVersion(self, version, major, minor, underDevelopment):
        self.assertTrue(version.hasMajor(major))
        self.assertTrue(version.hasMinor(minor))
        self.assertTrue(version.isUnderDevelopment())

    def testPrepareDevelopmentRelease(self):
        v1 = self.makeVersion("1.0.dev1")
        v2 = v1.nextDevelopmentRelease()
        self.verifyVersion(v2, 1, 0, 2)

    def testPrepareMinorRelease(self):
        v1 = self.makeVersion("1.0")
        v2 = v1.nextMinorRelease()
        self.verifyVersion(v2, 1, 1, True)
        
    def testPrepareMajorRelease(self):
        v1 = self.makeVersion("1.0")
        v2 = v1.nextMajorRelease()
        self.verifyVersion(v2, 2, 0, True)
        
    def testIsNotUnderDevelopment(self):
        version = self.makeVersion("1.2")
        self.assertFalse(version.isUnderDevelopment())

    def testIsUnderDevelopment(self):
        version = self.makeVersion("1.2.dev1")
        self.assertTrue(version.isUnderDevelopment())
        
    def testEquality(self):
        v1 = self.makeVersion("1.3.dev1")
        self.assertTrue(v1 == v1)

    def testDifference(self):
        v1 = self.makeVersion("1.3.dev2")
        v2 = self.makeVersion("1.3.dev3")
        self.assertTrue(v1 != v2)


class ReleaseTest(TestCase):
    
    def testDevelopmentRelease(self):
        sources = Sources()
        sources.readVersion = MagicMock()
        sources.readVersion.return_value = Version.fromText("1.3.dev3")
        sources.writeVersion = MagicMock()
                
        scm = SourceControl()
        scm.tag = MagicMock()
        scm.commit = MagicMock()
        
        release = Release(Distribution(), scm, sources)
        release.run()
        
        scm.tag.assert_called_once_with(Version(1, 3, 3))
        sources.readVersion.assert_called_once_with()
        sources.writeVersion.assert_called_once_with(Version(1, 3, 4))
        scm.commit.assert_has_calls([call("Releasing version 1.3.dev3"), 
                                     call("Preparing version 1.3.dev4")])
     
     
if __name__ == "__main__":
    main()