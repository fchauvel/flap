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

from flap import logger
from flap.util.path import Path
from flap.latex.symbols import SymbolTable
from flap.latex.parser import Parser, Factory, Context



class Settings:

    def __init__(self, file_system, ui, root_tex_file, output):
        self._file_system = file_system
        self._display = ui
        self._root_tex_file = root_tex_file
        self._output = output
        self._count = 0
        self._selected_for_inclusion = []
        self._graphic_directories = []
        self._analysed_dependencies = []

    @property
    def root_tex_file(self):
        return Path.fromText(self._root_tex_file)

    @property
    def root_directory(self):
        return self._file_system.open(self.root_tex_file).container()

    def record_graphic_path(self, paths, invocation):
        logger.debug("Updating graphicpath (" + invocation.as_text + ")")
        self._show_invocation(invocation)
        self._graphic_directories = [self._file_system.open(self.root_directory._path / each) for each in paths]

    @property
    def graphics_directory(self):
        return self._graphic_directories if self._graphic_directories else [self.root_directory]

    @property
    def read_root_tex(self):
        return self._file_system.open(self.root_tex_file).content()

    @property
    def output_directory(self):
        return Path.fromText(self._output)

    @property
    def flattened(self):
        return self.output_directory / "merged.tex"

    def execute(self):
        flattened = self._rewrite(self.read_root_tex, str(self.root_tex_file.resource()))
        self._write(flattened)

    def _rewrite(self, text, source, symbol_table=SymbolTable.default()):
        factory = Factory(symbol_table)
        parser = Parser(factory.as_tokens(text, source),
                        factory, self, Context())
        return parser.rewrite()

    def _write(self, tokens):
        latex_code = "".join(str(each_token) for each_token in tokens)
        self._file_system.create_file(self.flattened, latex_code)

    def relocate_dependency(self, dependency, invocation):
        if dependency not in self._analysed_dependencies:
            self._analysed_dependencies.append(dependency)
            try:
                file = self._find(dependency, [self.root_directory], ["sty", "cls"], TexFileNotFound(None))
                self._file_system.copy(file,
                                       self.output_directory / file.fullname())

                self._show_invocation(invocation)
                symbol_table = SymbolTable.default()
                symbol_table.CHARACTER += '@'
                self._rewrite(file.content(), file.fullname(), symbol_table)

            except TexFileNotFound:
                logger.debug("Could not find class or package '" + dependency + " locally")

    def content_of(self, location, invocation):
        logger.debug("Fetching '" + location + "(" + invocation.as_text + ")")
        self._show_invocation(invocation)
        file = self._find(location, [self.root_directory], ["tex"], TexFileNotFound(None))
        return file.content()

    def update_link(self, path, invocation):
        return self._update_link(path, invocation, self.graphics_directory, ["pdf", "png", "jpeg"], GraphicNotFound(None))

    def update_link_to_bibliography(self, path, invocation):
        return self._update_link(path, invocation, [self.root_directory], ["bib"], ResourceNotFound(None))

    def update_link_to_bibliography_style(self, path, invocation):
        return self._update_link(path, invocation, [self.root_directory], ["bst"], ResourceNotFound(None))

    def update_link_to_index_style(self, path, invocation):
        return self._update_link(path, invocation, [self.root_directory], ["ist"], ResourceNotFound(path)) + ".ist"

    def _update_link(self, path, invocation, location, extensions, error):
        logger.debug("Updating '" + path + "(" + invocation.as_text + ")")
        self._show_invocation(invocation)
        resource = self._find(path, location, extensions, error)
        new_path = resource._path.relative_to(self.root_directory._path)
        new_file_name = str(new_path).replace("/", "_")
        self._file_system.copy(resource, self.output_directory / new_file_name)
        return str(new_path.without_extension()).replace("/", "_")

    def include_only(self, selection, invocation):
        logger.debug("Restrict inclusion to [" + ", ".join(selection) + "] (" + invocation.as_text + ")")
        self._show_invocation(invocation)
        self._selected_for_inclusion.extend(selection)

    def shall_include(self, link):
        if len(self._selected_for_inclusion) == 0:
            return True
        else:
            return link in self._selected_for_inclusion

    def _show_invocation(self, invocation):
        self._count += 1
        self._display.entry(file=invocation.location.source,
                            line=invocation.location.line,
                            column=invocation.location.column,
                            code=invocation.as_text)

    @staticmethod
    def _find(path, directories, extensions, error):
        for any_directory in directories:
            candidates = any_directory.files_that_matches(Path.fromText(path))
            for any_possible_extension in extensions:
                for any_resource in candidates:
                    if any_resource.has_extension(any_possible_extension):
                        return any_resource
        raise error


class ResourceNotFound(Exception):

    def __init__(self, fragment):
        self._fragment = fragment

    def fragment(self):
        return self._fragment


class GraphicNotFound(ResourceNotFound):
    """
    Exception thrown when a graphic file cannot be found
    """
    def __init__(self, fragment):
        super().__init__(fragment)


class TexFileNotFound(ResourceNotFound):
    """
    Exception thrown when a LaTeX source file cannot be found
    """

    def __init__(self, fragment):
        super().__init__(fragment)