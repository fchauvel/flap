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
from flap.util import truncate
from flap.util.path import Path
from flap.latex.symbols import SymbolTable
from flap.latex.macros.factory import MacroFactory
from flap.latex.parser import Parser, Factory, Context


def log(invocation, message, **kwargs):
    data = (invocation.location.source,
            str(invocation.location.line),
            str(invocation.location.column),
            repr(truncate(invocation.as_text, length=40)),
            message.format(**kwargs))
    logger.debug(" ".join(data))


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
        log(invocation, "Updating graphicpath to {paths:s}", paths=repr(paths))
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
        tokens = self._rewrite(self.read_root_tex, str(self.root_tex_file.resource()))
        self._write(tokens, self.flattened)

    def _rewrite(self, text, source, symbol_table=SymbolTable.default()):
        factory = Factory(symbol_table)
        macros = MacroFactory(self)
        parser = Parser(factory.as_tokens(text, source),
                        factory,
                        Context(definitions=macros.all()))
        return parser.rewrite()

    def _write(self, tokens, destination):
        latex_code = "".join(str(each_token) for each_token in tokens)
        self._file_system.create_file(destination, latex_code)

    def end_of_input(self, source, invocation):
        self._show_invocation(invocation)
        log(invocation, "Skipping the rest of '{source}'", source=source)

    def relocate_dependency(self, dependency, invocation):
        if dependency not in self._analysed_dependencies:
            self._analysed_dependencies.append(dependency)
            try:
                file = self._find(dependency, [self.root_directory], ["sty", "cls"], TexFileNotFound(None))
                new_path = file._path.relative_to(self.root_directory._path)
                self._show_invocation(invocation)
                symbol_table = SymbolTable.default()
                symbol_table.CHARACTER += '@'
                tokens = self._rewrite(file.content(), file.fullname(), symbol_table)
                self._write(tokens, self.output_directory / self._as_file_name(new_path))
                return self._as_file_name(new_path.without_extension())

            except TexFileNotFound:
                log(invocation,
                    "Could not find class or package '{path:s}' locally",
                    path=dependency)
                return None

    def content_of(self, location, invocation):
        self._show_invocation(invocation)
        file = self._find(location, [self.root_directory], ["tex"], TexFileNotFound(location))
        log(invocation, "Fetching content from '{file:s}'", file=file.fullname())
        return file.content()

    def update_link(self, path, invocation):
        extensions = ["pdf", "png", "jpeg", "jpg", "ps", "eps", "svg"]
        return self._update_link(path,
                                 invocation,
                                 self.graphics_directory,
                                 extensions,
                                 GraphicNotFound(path))

    def update_link_to_bibliography(self,
                                    path,
                                    invocation,
                                    keep_file_extension=False):
        return self._update_link(path,
                                 invocation,
                                 [self.root_directory],
                                 ["bib"],
                                 ResourceNotFound(path),
                                 keep_file_extension)

    def update_link_to_bibliography_style(self, path, invocation):
        try:
            return self._update_link(path,
                                     invocation,
                                     [self.root_directory],
                                     ["bst"],
                                     ResourceNotFound(path))

        except ResourceNotFound:
            log(invocation,
                "Could not find bibliography style '{path:s}' locally",
                path=path)
            return path

    def update_link_to_index_style(self, path, invocation):
        return self._update_link(path,
                                 invocation,
                                 [self.root_directory],
                                 ["ist"], ResourceNotFound(path)) + ".ist"

    def _update_link(self,
                     path,
                     invocation,
                     location,
                     extensions,
                     error,
                     keep_file_extension=False
                     ):
        self._show_invocation(invocation)
        resource = self._find(path, location, extensions, error)
        new_path = self._move(resource, invocation)
        if keep_file_extension:
            return self._as_file_name(new_path)
        else:
            return self._as_file_name(new_path.without_extension())

    def _move(self, file, invocation):
        new_path = file._path.relative_to(self.root_directory._path)
        new_file_name = self._as_file_name(new_path)
        self._file_system.copy(file, self.output_directory / new_file_name)
        log(invocation, "Copying '{source:s}' to '{target:s}'",
            source=file.fullname(), target=new_file_name)
        return new_path

    @staticmethod
    def _as_file_name(path):
        return str(path).replace("../", "").replace("/", "_")

    def include_only(self, selection, invocation):
        log(invocation, "Restricting file inclusions to {files:s}", files=repr(selection))
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
