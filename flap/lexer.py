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

import re

class Position:
    
    def __init__(self, line, column):
        self._line = line
        self._column = column 
        
    def nextLine(self):
        return Position(self._line + 1, 1)

    def nextColumn(self):
        return Position(self._line, self._column + 1)
    
    def __eq__(self, other):
        return self._line == other._line and self._column == other._column 
    
    def __repr__(self):
        return "(%d, %d)" % (self._line, self._column)


class Fragment:
    TEXT = "text"
    SYMBOL = "symbol"
    COMMENT = "comment"
    
    def __init__(self, buffer, kind):
        self._position = buffer.position()
        self._text = buffer.text()
        self._kind = kind
    
    def text(self):
        return self._text
    
    def type(self):
        return self._kind
    
    def position(self):
        return self._position
    
    def __repr__(self):
        return "(%s@%s: '%s')" % (self._kind.upper(), self._position, self._text)


class Source:
    pass


class Reader:
    
    def __init__(self, text):
        self._cursor = Cursor(text) 
        self._buffer = []
        self._position = Position(1, 0)

    def isEmpty(self):
        return len(self._buffer) == 0
    
    def text(self):
        return ''.join(self._buffer)

    def position(self):
        return self._position

    def clear(self):    
        self._buffer = []
        
    def current(self):
        return self._cursor.current()
    
    def isDefined(self):
        return self._cursor.isDefined()
    
    def read(self):
        if self._cursor.isDefined():
            self._append()
            self._cursor.next()

    def _append(self):
        if not self._buffer:
            self._position = self._cursor.position()
        self._buffer.append(self._cursor.current())
            
    def __repr__(self):
        return "%s :: %s" % (self._cursor.current(), self._buffer)

    
class Cursor:
    
    def __init__(self, text):
        self._characters = iter(text)
        self._position = Position(1, 0)
        self._current = None
        self.next()
        
    def position(self):
        return self._position
        
    def current(self):
        return self._current
    
    def next(self):
        if self._current == "\n":
            self._position = self._position.nextLine()
        else:
            self._position = self._position.nextColumn()
        self._current = next(self._characters, None)
      
    def isDefined(self):
        return self._current is not None

    def __repr__(self):
        return self._current


class Rule:
    
    def applyTo(self, reader):
        pass


class DefaultRule(Rule):
    
    def applyTo(self, reader):
        reader.read()
        return []


class RuleExtension(Rule):
    
    def __init__(self, default):
        self._default = default 
        self._factory = FragmentFactory()
      
    def applyTo(self, reader):
        if self._match(reader):
            yield from self._proceed(reader)
        else:
            yield from self._default.applyTo(reader)
            
    def _match(self, reader):
        pass
    
    def _proceed(self, reader):
        pass


class Symbols(RuleExtension):
    
    def __init__(self, delegate):
        super().__init__(delegate)
        self._symbols = ["{", "}", "[", "]", "\n"]
        
    def _match(self, reader):
        return reader.current() in self._symbols

    def _proceed(self, reader):
        yield from self._factory.makeFragment(reader)
        reader.read()
        yield from self._factory.makeSymbol(reader)
        reader.clear()
    
    
class Comments(RuleExtension):
    
    def __init__(self, delegate):
        super().__init__(delegate)
        self._comments = {"start": ["%"], "end": ["\n"] }
         
    def _match(self, reader):
        return reader.current() in self._comments["start"]
    
    def _proceed(self, reader):
        yield from self._factory.makeFragment(reader)
        while not self._endsComment(reader):
            reader.read()
        yield from self._factory.makeComment(reader)
        reader.clear()
    
    def _endsComment(self, character):
        return (character.current() is None 
                or character.current() in self._comments["end"])
    

class FragmentFactory:
    
    def __init__(self):
        self._types = { "command": re.compile(r"\\\w+") }
        
    def makeComment(self, reader):
        return [Fragment(reader, Fragment.COMMENT)]
        
    def makeSymbol(self, reader):
        return [Fragment(reader, Fragment.SYMBOL)]
        
    def makeFragment(self, reader):
        if not reader.isEmpty():
            fragment = self._buildFragment(reader)
            reader.clear()
            return [fragment]
        return []

    def _buildFragment(self, reader):
        for (kind, pattern) in self._types.items():
            if pattern.match(reader.text()):
                return Fragment(reader, kind)
            return Fragment(reader, Fragment.TEXT)
        
    
class Lexer:
    
    def __init__(self, source):
        self._factory = FragmentFactory()
        self._rules = Symbols(Comments(DefaultRule()))
        self._source = source
    
        
    def breakUp(self):
        reader = Reader(self._source.text())
        while reader.isDefined():
            yield from self._rules.applyTo(reader)
        yield from self._factory.makeFragment(reader)    
                
   
