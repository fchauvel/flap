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

from unittest import TestCase
from flap.ui import main
from flap.path import TEMP
from flap.engine import Flap


TEST_DIRECTORY = TEMP / "flap-tests"


class LatexProject:
    """
    Data needed to defined the structure and content of a LaTeX project
    """

    IMAGE_CONTENT = "fake image content"
    RESOURCE_CONTENT = "fake resource content"

    def __init__(self):
        self.directory = TEST_DIRECTORY / "project"
        self.root_latex_file = "main.tex"
        self.root_latex_code = "some latex code"
        self.parts = {}
        self.images_directory = "images"
        self.images = []
        self.resources = []

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, path):
        self._directory = path

    @property
    def root_latex_file(self):
        return self._root_latex_file

    @root_latex_file.setter
    def root_latex_file(self, path):
        self._root_latex_file = self._directory / path

    def create_on(self, file_system):
        file_system.deleteDirectory(self.directory)
        file_system.createFile(self.root_latex_file, self.root_latex_code)
        for (path, content) in self.parts.items():
            file_system.createFile(self.directory / path, content)
        for eachImage in self.images:
            file_system.createFile(self.directory / eachImage, LatexProject.IMAGE_CONTENT)
        for eachResource in self.resources:
            file_system.createFile(self.directory / eachResource, LatexProject.RESOURCE_CONTENT)


class FlapTest(TestCase):
    """
    Run and provides helpers to verify the outputs produced by FLaP
    """

    def setUp(self):
        self.file_system = None
        self.project = LatexProject()
        self.output_directory = TEST_DIRECTORY / "output"
        self.working_directory = TEST_DIRECTORY
        self.merged_file = Flap.DEFAULT_OUTPUT_FILE

    def run_flap(self, output):
        self.output_directory = TEST_DIRECTORY / output
        if self.output_directory.hasExtension():
            self.merged_file = self.output_directory.fullname()
            self.output_directory = self.output_directory.container()
        pass

    def verify_merge(self, expected):
        self.assertEqual(self._content_of(self.merged_file), expected)

    def _content_of(self, path):
        return self.file_system.open(self.output_directory / path).content()

    def verify_images(self):
        for eachImage in self.project.images:
            self.verify_image(eachImage)

    def verify_image(self, image):
        self.assertEqual(self._content_of(image), LatexProject.IMAGE_CONTENT)

    def verify_resources(self, expected_content=LatexProject.RESOURCE_CONTENT):
        for eachResource in self.project.resources:
            self.assertEqual(self._content_of(eachResource), expected_content)


