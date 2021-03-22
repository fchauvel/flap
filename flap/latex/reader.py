from flap import logger
from flap.latex.lexer import Lexer
from flap.latex.commons import Context, Stream


def peel(stream):
    if isinstance(stream, Lexer):
        return stream
    elif isinstance(stream, Stream):
        return peel(stream._source,)
    elif isinstance(stream, list):
        raise RuntimeError("Found a damned list!")
    raise RuntimeError("Expecting Lexer, but found: " + str(type(stream)))


class Reader:

    def __init__(self, lexer, factory):
        self._tokens = peel(lexer)
        self._name = "READER"
        self._outputs = [[]]
        self._cache = []

    def process_control(self, token):
        self._default(token)

    def process_begin_group(self, token):
        self._default(token)

    def process_end_group(self, end_group):
        self._default(end_group)

    def process_character(self, character):
        self._default(character)

    def process_comment(self, comment):
        self._default(comment)

    def process_parameter(self, parameter):
        self._default(parameter)

    def process_white_spaces(self, space):
        self._default(space)

    def process_new_line(self, new_line):
        self._default(new_line)

    def process_others(self, other):
        self._default(other)

    def process_invocation(self, invocation):
        self._default(invocation)

    def _default(self, token):
        self._log("On " + str(token))
        self._print([token])


    # Methods that manage the output

    def _print(self, tokens):
        self._output.extend(tokens)

    def push_new_output(self):
        self._log("Setup new output")
        self._outputs.append([])

    def pop_output(self):
        self._log("Discarding current output: " + self.output_as_text())
        return self._outputs.pop()

    def output_as_text(self):
        return "".join(each_token.as_text
                       for each_token in self._output)

    def _clear_output(self):
        output = list(self._outputs[-1])
        self._outputs[-1] = []
        self._log("Captured so far: '" + "".join(str(t) for t in output) + "'")
        return output

    @property
    def _output(self):
         return self._outputs[-1]

    def _log(self, message):
        logger.debug(f"{self._name}: {message}")

    # Mirroring Stream

    @property
    def is_empty(self):
        return len(self._cache) == 0 and self._tokens._next is None

    def take(self):
        if self._cache:
            return self._cache.pop()
        return self._tokens._one_token()

    @property
    def look_ahead(self):
        if self._cache:
            return self._cache[-1]
        if self._tokens._next is not None:
            token = self._tokens._one_token()
            self._cache.append(token)
            return token
        raise RuntimeError("No more character to read!")

    @property
    def _next_token(self):
        return self.look_ahead    # Real methods

    def one(self):
        self._log("Reading one ...")
        if not self.is_empty:
            token = self.take()
            token.send_to(self)
            return self._clear_output()
        raise RuntimeError("No more tokens!")

    def group(self):
        self._log("Reading group ...")
        self.until(lambda t: not t.is_ignored)
        self.only_if(lambda t: t.begins_a_group)
        return self._clear_output()

    def only_if(self, is_expected):
        self._log("Reading only if  ...")
        if not self.is_empty:
            if is_expected(self.look_ahead):
                token = self.take()
                token.send_to(self)
            else:
                self._raise_unexpected_token("not specified", token)

    def until(self, is_end):
        self._log("Reading until ...")
        while not self.is_empty:
            if is_end(self.look_ahead):
                break
            else:
                token = self.take()
                token.send_to(self)
        return self._clear_output()

    def until_group(self):
        output = self.until(lambda t: t.begins_a_group)
        self._print(output)
        return self._clear_output()

    def options(self, start="[", end="]"):
        self._log("Reading options ...")
        tokens = []
        try:
            tokens += self.until(lambda t: not t.is_ignored)
            self.only_if(lambda token: token.has_text(start))
            tokens += self.until_text(end)
            self.only_if(lambda token: token.has_text(end))
            tokens += self.until(lambda t: not t.is_ignored)
            tokens += self._clear_output()
            return tokens
        except ValueError as error:
            self._log("Error '%s'" % str(error))
            return []

    def macro_name(self, name=None):
        self._log("Reading macro name!")
        self.only_if(lambda token: token.is_a_command)
        if name and not self._output[-1].ends_with(name):
            self._raise_unexpected_token()
        return self._clear_output()

    def ignored(self):
        while self._next_token \
              and self._next_token.is_ignored:
            token = self._tokens.take()
            token.send_to(self)
        return self._clear_output()

    def text(self, marker):
        self._log("Reading text '%s'" % marker)
        text = ""
        while self._next_token:
            text += str(self.look_ahead)
            if not marker.startswith(text):
                break
            token = self._tokens.take()
            token.send_to(self)
        return self._clear_output()

    def until_text(self, marker, capture_marker=False):
        self._log("Reading until text '%s' ..." % marker)
        text = ""
        while not self.is_empty:
            text += str(self.look_ahead)
            if text.endswith(marker):
                if capture_marker:
                    token = self.take()
                    self._print([token])
                break
            self._print([token])
        return self._clear_output()

    def _raise_unexpected_token(self, expected, actual):
        error = (
            "Expected {}, but found '{}' in file {} (l. {}, col. {})"
        ).format(
            expected,
            actual,
            actual.location.source,
            actual.location.line,
            actual.location.column)
        self._tokens.debug()
        raise ValueError(error)

    def _default(self, token):
        self._print([token])

    def process_control(self, token):
        self._default(token)

    def process_begin_group(self, token):
        self._log("On begin group")
        self.push_new_output()
        self._print([token])
        content = self.until(lambda t: t.ends_a_group)
        self._print(content)
        self.only_if(lambda t: t.ends_a_group)

    def process_end_group(self, end_group):
        self._log("On end group")
        self._print([end_group])
        group_tokens = self.pop_output()
        self._print(group_tokens)

    def process_invocation(self, invocation):
        raise RuntimeError("Reader should never meet an invocation token!")
