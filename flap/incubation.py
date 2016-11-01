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

from flap import __version__

from flap.util.path import Path
from flap.latex.symbols import SymbolTable
from flap.latex.parser import Parser, Factory, Context


class Display:

    PADDING = "-"

    FILE_WIDTH = 30
    LINE_WIDTH = 5
    COLUMN_WIDTH = 6
    CODE_WIDTH = 35

    ENTRY = "{file:<%d} {line:>%d} {column:>%d} {code:<%d}\n" % (FILE_WIDTH, LINE_WIDTH, COLUMN_WIDTH, CODE_WIDTH)
    HEADER = ENTRY.format(file="File", line="Line", column="Column", code="LaTeX Command")
    SUMMARY = "{count} modification(s)"

    def __init__(self, output):
        self._output = output

    def version(self):
        self._output.write("FLaP v%s\n" % __version__)

    def header(self):
        self._show(self.HEADER)
        self._show(self._horizontal_line())

    def entry(self, file, line, column, code):
        self._show(self.ENTRY, file=file, line=line, column=column, code=code)

    def footer(self):
        self._show(self._horizontal_line())
        self._show(self.SUMMARY, count=1)

    def _horizontal_line(self):
        return self.ENTRY.format(
                   file=self._pad(self.FILE_WIDTH),
                   line=self._pad(self.LINE_WIDTH),
                   column=self._pad(self.COLUMN_WIDTH),
                   code=self._pad(self.CODE_WIDTH))

    @classmethod
    def _pad(cls, length):
        return "".ljust(length, cls.PADDING)

    def _show(self, template, **values):
        self._output.write(template.format(**values))


class Settings:

    def __init__(self, file_system, ui, root_tex_file, output):
        self._file_system = file_system
        self._display = ui
        self._root_tex_file = root_tex_file
        self._output = output

    @property
    def root_tex_file(self):
        return Path.fromText(self._root_tex_file)

    @property
    def root_directory(self):
        return self._file_system.open(self.root_tex_file).container()

    @property
    def graphics_directory(self):
        return self.root_directory

    @property
    def read_root_tex(self):
        return self._file_system.open(self.root_tex_file).content()

    @property
    def output_directory(self):
        return Path.fromText(self._output)

    @property
    def flattened(self):
        return self.output_directory / "merged.tex"

    def write(self, tokens):
        latex_code =  "".join(str(each_token) for each_token in tokens)
        self._file_system.create_file(self.flattened, latex_code)

    def content_of(self, location, invocation):
        self._show_invocation(invocation)
        return self._file_system.open(Path.fromText(location)).content()

    def update_link(self, path, invocation):
        self._show_invocation(invocation)
        resource = self.find_graphics(None, path)
        new_path = resource._path.relative_to(self.root_directory._path)
        new_file_name = str(new_path).replace("/", "_")
        self._file_system.copy(resource, self.output_directory / new_file_name)
        return str(new_path.without_extension()).replace("/", "_")

    def _show_invocation(self, invocation):
        self._display.entry(file="test.tex",
                            line=invocation.location.line,
                            column=invocation.location.column,
                            code=invocation.as_text)

    def find_graphics(self, fragment, path):
        return self._find(path, self.graphics_directory, ["pdf", "png", "jpeg"], GraphicNotFound(fragment))

    @staticmethod
    def _find(path, directory, extensions, error):
        candidates = directory.files_that_matches(Path.fromText(path))
        for any_possible_extension in extensions:
            for any_resource in candidates:
                if any_resource.has_extension(any_possible_extension):
                    return any_resource
        raise error


class Controller:

    def __init__(self, file_system, display):
        self._file_system = file_system
        self._display = display

    def run(self, arguments):
        self._display.version()
        self._display.header()
        settings = self._parse(arguments)
        self._flatten(settings)
        self._display.footer()

    @staticmethod
    def _flatten(flap):
        factory = Factory(SymbolTable.default())
        parser = Parser(factory.as_tokens(flap.read_root_tex), factory, flap, Context())
        flap.write(parser.rewrite())

    def _parse(self, arguments):
        assert len(arguments) == 3, "Expected 3 arguments, but found %s" % arguments
        return Settings(file_system=self._file_system,
                        ui = self._display,
                        root_tex_file=arguments[1],
                        output=arguments[2])


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