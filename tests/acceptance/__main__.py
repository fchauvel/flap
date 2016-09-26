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

from sys import stdout

from flap.util.oofs import OSFileSystem
from flap.util.path import Path, TEMP
from io import StringIO
from tests.acceptance.engine import FileBasedTestRepository, YamlCodec, TestRunner, Acceptor

file_system = OSFileSystem()
repository = FileBasedTestRepository(file_system, Path.fromText("tests/acceptance/tests"), YamlCodec())
runner = TestRunner(file_system, TEMP / "flap" / "acceptance")
output = StringIO()
Acceptor(repository, runner, stdout).check()
