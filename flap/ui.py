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

import sys
import click

from flap import __version__, __tool_name__
from flap.util import truncate
from flap.util.oofs import OSFileSystem
from flap.engine import Settings


class Controller:

    def __init__(self, file_system, display):
        self._file_system = file_system
        self._display = display

    def run(self, tex_file, output):
        request = Settings(
            file_system=self._file_system,
            ui=self._display,
            root_tex_file=tex_file,
            output=output)
        self._display.version()
        self._display.header()
        request.execute()
        self._display.footer(request._count, output)


class Display:

    WIDTHS = (30, 5, 6, 35)

    VERSION = "{name} {version}\n"
    ENTRY = "{file:<%d} {line:>%d} {column:>%d} {code:<%d}\n" % WIDTHS
    HEADER = ENTRY.format(file="File",
                          line="Line",
                          column="Column",
                          code="LaTeX Command")
    SUMMARY = "{count} modification(s)\n"
    CLOSING = "Check out your flattened project in '{directory}'.\n"

    def __init__(self, output, verbose=False):
        self._output = output
        self._verbose = verbose

    def version(self):
        self._show(self.VERSION, name=__tool_name__, version=__version__)

    def header(self):
        if self._verbose:
            self._show(self.HEADER)
            self._show(self._horizontal_line())

    def entry(self, file, line, column, code):
        if self._verbose:
            escaped_code = truncate(code.strip().replace("\n", r"\n"),
                                    length=self.WIDTHS[3])
            self._show(self.ENTRY, file=file,
                       line=line,
                       column=column,
                       code=escaped_code)

    def footer(self, count, output):
        if self._verbose:
            self._show(self._horizontal_line())
        self._show(self.SUMMARY, count=count)
        self._show(self.CLOSING, directory=output)

    def _horizontal_line(self):
        return "-" * (sum(self.WIDTHS) + len(self.WIDTHS)-1) + "\n"

    def _show(self, template, **values):
        self._output.write(template.format(**values))


@click.command()
@click.argument('tex_file',
                type=click.Path(exists=True,
                                file_okay=True,
                                dir_okay=False))
@click.argument('output',
                type=click.Path(file_okay=False, dir_okay=True))
@click.option("-v",
              "--verbose",
              is_flag=True,
              help='Details what FLaP is doing')
def main(tex_file, output, verbose):
    """FLaP merges your LaTeX projects into a single LaTeX file that
    refers to images in the same directory.

    It reads the given root TEX_FILE and generates a flatten version
    in the given OUTPUT directory. It inlines the content of any TeX
    files refered by \\input or \\include but also copies resources
    such as images (JPG, EPS, PDF, etc.) as well as other resources
    (class and package definitions, BibTeX files, etc.).

    """
    Controller(OSFileSystem(), Display(sys.stdout, verbose))\
        .run(tex_file, output)


# For compatibility with versions prior to 0.2.3
if __name__ == "__main__":
    main(*sys.argv)
