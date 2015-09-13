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


class LatexProjectBuilder:
    """
    Helps build the file structure of a LaTeX project.
    It does not contain any test, but it uses assertions
    """

    IMAGE_CONTENT = "image data"
    STYLE_CONTENT = "some style definitions"
    CLASS_CONTENT = "a class definition"

    def __init__(self, file_system):
        self._file_system = file_system
        self.directory = TEMP / "project"
        self.main_latex_file = "main.tex"
        self.images_directory = "images"

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, path):
        self._directory = path

    @property
    def main_latex_file(self):
        return self._main_latex_file

    @main_latex_file.setter
    def main_latex_file(self, path):
        self._main_latex_file = self._directory / path

    @property
    def images_directory(self):
        return self._images_directory

    @images_directory.setter
    def images_directory(self, path):
        self._images_directory = self._directory / path

    def clear(self):
        self._file_system.deleteDirectory(self._directory)

    def create_root_latex_file(self, content):
        self._file_system.createFile(self._main_latex_file, content)

    def create_latex_file(self, path, content):
        self._file_system.createFile(self._directory / path, content)

    def create_image(self, path):
        self._file_system.createFile(self._images_directory / path, LatexProjectBuilder.IMAGE_CONTENT)

    def create_style_file(self, path):
        self._file_system.createFile(self._directory / path, LatexProjectBuilder.STYLE_CONTENT)

    def create_class_file(self, path):
        self._file_system.createFile(path, "a class definition")

    def create_symbolic_link(self, link_path, link_target):
        symlink(self._file_system.forOS(link_target), self._file_system.forOS(self._directory / link_path))

    @property
    def path_to_root_latex_file(self):
        return self._file_system.forOS(self._main_latex_file)


class FlapRunner:
    """
    Invoke FLaP, and provides access to the outputted files
    """

    def __init__(self, latex_project, working_directory, output_directory):
        self._project = latex_project
        self.working_directory = working_directory
        self.output_directory = output_directory
        self.merged_file = "merged.tex"

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, path):
        self._working_directory = path

    @property
    def output_directory(self):
        return self._output_directory

    @output_directory.setter
    def output_directory(self, directory):
        self._output_directory = directory

    @property
    def merged_file(self):
        return self.output_directory / self._merged_file

    @merged_file.setter
    def merged_file(self, path):
        self._merged_file = path

    def run_flap(self):
        root = self._project.path_to_root_latex_file
        output = self._project._file_system.forOS(self.output_directory)
        main(["-v", root, output])

    def merged_content(self):
        return self.content_of(self._merged_file)

    def content_of(self, path):
        return self._project._file_system.open(self.output_directory / path).content()


class FlapVerifier(TestCase):
    """
    Verify the outputs produced by FLaP
    """

    def __init__(self, file_system, runner):
        super().__init__()
        self._file_system = file_system
        self._runner = runner

    def merged_content_is(self, expected):
        self.assertEqual(self._runner.merged_content(), expected)

    def style_file(self, path):
        self.assertEqual(self._runner.content_of(path), LatexProjectBuilder.STYLE_CONTENT)

    def class_file(self, path):
        self.assertEqual(self._runner.content_of(path), LatexProjectBuilder.CLASS_CONTENT)

