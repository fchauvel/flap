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
from mock import Mock, MagicMock, call, patch, ANY, mock_open

from flap.util import Version, Release, SourceControl
from distutils.dist import Distribution


class VersionTest(TestCase):
    
    def makeVersion(self, text):
        return Version.fromText(text)

    def verifyVersion(self, version, major, minor, micro):
        self.assertTrue(version.hasMajor(major))
        self.assertTrue(version.hasMinor(minor))
        self.assertTrue(version.hasMicro(micro))

    def testPrepareDevelopmentRelease(self):
        v1 = self.makeVersion("1.0.1")
        v2 = v1.nextMicroRelease()
        self.verifyVersion(v2, 1, 0, 2)

    def testPrepareMinorRelease(self):
        v1 = self.makeVersion("1.0")
        v2 = v1.nextMinorRelease()
        self.verifyVersion(v2, 1, 1, 0)
        
    def testPrepareMajorRelease(self):
        v1 = self.makeVersion("1.0")
        v2 = v1.nextMajorRelease()
        self.verifyVersion(v2, 2, 0, 0)
                
    def testEquality(self):
        v1 = self.makeVersion("1.3.dev1")
        self.assertTrue(v1 == v1)

    def testDifference(self):
        v1 = self.makeVersion("1.3.dev2")
        v2 = self.makeVersion("1.3.dev3")
        self.assertTrue(v1 != v2)

    def test_read_from_source_code(self):
        with patch("flap.__version__", "1.3.4"):
            version = Version.from_source_code()
            self.assertEqual(version, Version(1, 3, 4))

    def test_update_source_code(self):
        mock = mock_open(read_data="__version__ = \"1.2.3\"")
        with patch('flap.util.open', mock, create=True):
            Version.update_source_code(Version(1, 3, 0))
        mock().write.assert_called_once_with("__version__ = \"1.3.0\"")




class SourceControlTest(TestCase):
    
    def test_commit(self):
        mock = MagicMock()
        with patch("subprocess.call", mock):
            scm = SourceControl()
            scm.commit("my message")
        mock.assert_has_calls([call(["git.exe", "add", "-u"], env=ANY, shell=True),
                               call(["git.exe", "commit", "-m", "my message"], env=ANY, shell=True)])

    def test_tag(self):
        mock = MagicMock()
        with patch("subprocess.call", mock):
            scm = SourceControl()
            scm.tag(Version(2, 0, 1))
        mock.assert_has_calls([call(["git.exe", "tag", "-a", "v2.0.1", "-m", "\"Version 2.0.1\""], env=ANY, shell=True)])


class ReleaseTest(TestCase):
    
    def createSourceWithVersion(self, text):
        return None

    def release(self, scm, kind):
        release = Release(Distribution(), scm)
        release.run_command = MagicMock()
        release.type = kind
        release.run()
        return release
    
    def createSCM(self):
        scm = SourceControl()
        scm.tag = MagicMock()
        scm.commit = MagicMock()
        return scm

    def _verify_command_invocations(self, release):
        release.run_command.assert_has_calls([
            call("bdist_egg"),
            call("sdist"),
            call("register"),
            call("upload"),
        ])

    @patch("flap.util.Version.from_source_code", return_value=Version(1, 3, 3))
    @patch("flap.util.Version.update_source_code")
    def testMicroRelease(self, write_version, read_version):
        scm = self.createSCM()

        release = self.release(scm, "micro")

        self._verify_command_invocations(release)

        scm.tag.assert_called_once_with(Version(1, 3, 3))
        read_version.assert_called_once_with()
        write_version.assert_called_once_with(Version(1, 3, 4))
        scm.commit.assert_called_once_with("Preparing version 1.3.4")\

    @patch("flap.util.Version.from_source_code", return_value=Version(1, 3, 3))
    @patch("flap.util.Version.update_source_code")
    def testMinorRelease(self, write_version, read_version):
        scm = self.createSCM()
        
        release = self.release(scm, "minor")

        self._verify_command_invocations(release)

        read_version.assert_called_once_with()
        scm.tag.assert_called_once_with(Version(1, 4, 0))
        write_version.assert_has_calls([call(Version(1,4,0)),
                                               call(Version(1,4,1))])
        scm.commit.assert_has_calls([call("Releasing version 1.4.0"), 
                                     call("Preparing version 1.4.1")])

    @patch("flap.util.Version.from_source_code", return_value=Version(1, 3, 3))
    @patch("flap.util.Version.update_source_code")
    def testMajorRelease(self, write_version, read_version):
        scm = self.createSCM()
        
        release = self.release(scm, "major")

        self._verify_command_invocations(release)

        read_version.assert_called_once_with()
        scm.tag.assert_called_once_with(Version(2, 0, 0))
        write_version.assert_has_calls([call(Version(2, 0, 0)), call(Version(2,0,1))])
        scm.commit.assert_has_calls([call("Releasing version 2.0.0"), 
                                     call("Preparing version 2.0.1")])
     
     
if __name__ == "__main__":
    main()