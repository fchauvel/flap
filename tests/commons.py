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

from os import symlink
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

    @property
    def images_directory(self):
        return self._images_directory

    @images_directory.setter
    def images_directory(self, path):
        if path is None:
            self._images_directory = self.directory
        else:
            self._images_directory = self._directory / path

    def path_to_image(self, image):
        assert image in self.images, "Unknown image '%s'! Candidates images are '%s'" % (image, self.images)
        return self.images_directory / image

    def create_on(self, file_system):
        file_system.deleteDirectory(self.directory)
        file_system.createFile(self.root_latex_file, self.root_latex_code)
        for (path, content) in self.parts.items():
            file_system.createFile(self.directory / path, content)
        for eachImage in self.images:
            file_system.createFile(self.path_to_image(eachImage), LatexProject.IMAGE_CONTENT)
        for eachResource in self.resources:
            file_system.createFile(self.directory / eachResource, LatexProject.RESOURCE_CONTENT)


class FlapRunner:
    """
    Invoke FLaP, and provides access to the outputted files
    """

    def __init__(self, file_system):
        self._file_system = file_system
        self.output_directory = TEST_DIRECTORY / "output"
        self.working_directory = TEST_DIRECTORY

    @property
    def merged_file(self):
        return self.output_directory / Flap.OUTPUT_FILE

    def run_flap(self, project):
        root = self._file_system.forOS(project.root_latex_file)
        output = self._file_system.forOS(self.output_directory)
        main(["-v", root, output])

    def merged_content(self):
        return self.content_of(Flap.OUTPUT_FILE)

    def content_of(self, path):
        return self._file_system.open(self.output_directory / path).content()


class FlapVerifier(TestCase):
    """
    Verify the outputs produced by FLaP
    """

    def __init__(self, project, runner):
        super().__init__()
        self.project = project
        self._runner = runner

    def merged_content_is(self, expected):
        self.assertEqual(self._runner.merged_content(), expected)

    def images(self):
        for eachImage in self.project.images:
            self.image(eachImage)

    def image(self, image):
        self.assertEqual(self._runner.content_of(image), LatexProject.IMAGE_CONTENT)

    def resources(self):
        for eachResource in self.project.resources:
            self.assertEqual(self._runner.content_of(eachResource), LatexProject.RESOURCE_CONTENT)


