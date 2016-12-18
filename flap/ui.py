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
import argparse

from flap import __version__, __name__, logger
from flap.util.oofs import OSFileSystem
from flap.engine import Settings


class Controller:

    def __init__(self, file_system, display):
        self._file_system = file_system
        self._display = display

    def run(self, arguments):
        self._display.version()
        self._display.header()
        request = self._read_request_from(arguments)
        request.execute()
        self._display.footer(request._count)

    def _read_request_from(self, arguments):
        return Settings(file_system=self._file_system,
                        ui=self._display,
                        root_tex_file=arguments.file,
                        output=arguments.output)


class Display:

    PADDING = "-"

    FILE_WIDTH = 30
    LINE_WIDTH = 5
    COLUMN_WIDTH = 6
    CODE_WIDTH = 35

    ENTRY = "{file:<%d} {line:>%d} {column:>%d} {code:<%d}\n" % (FILE_WIDTH, LINE_WIDTH, COLUMN_WIDTH, CODE_WIDTH)
    HEADER = ENTRY.format(file="File", line="Line", column="Column", code="LaTeX Command")
    SUMMARY = "{count} modification(s)"

    CLASS_NOT_FOUND = " -> Warning: Could not find class '{name}' locally.\n\n"

    def __init__(self, output):
        self._output = output

    def version(self):
        self._output.write("%s v%s\n" % (__name__, __version__))

    def header(self):
        self._show(self.HEADER)
        self._show(self._horizontal_line())

    def entry(self, file, line, column, code):
        escaped_code = code.strip().replace("\n", r"\n")
        self._show(self.ENTRY, file=file, line=line, column=column, code=escaped_code)

    def class_not_found(self, class_name):
        self._show(self.CLASS_NOT_FOUND, name=class_name)

    def footer(self, count):
        self._show(self._horizontal_line())
        self._show(self.SUMMARY, count=count)

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='Path to the tex file.')
    parser.add_argument('output-dir', dest='output', help='Path to the output directory.')

    arguments = parser.parse_args()

    Controller(OSFileSystem(), Display(sys.stdout)).run(arguments)


# For compatibility with versions prior to 0.2.3
if __name__ == "__main__":
    main()
