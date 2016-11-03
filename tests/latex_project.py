class LatexProject:

    @staticmethod
    def extract_from_directory(root):
        files = LatexProject._collect_files_from(root, root)
        return LatexProject(*files)

    @staticmethod
    def _collect_files_from(anchor, directory):
        files = []
        for any_file in directory.files():
            if any_file.is_directory():
                files += LatexProject._collect_files_from(anchor, any_file)
            else:
                path = str(any_file.path().relative_to(anchor.path()))
                files.append(TexFile(path, any_file.content()))
        return files

    def __init__(self, *files):
        self._files = {each_file.path: each_file for each_file in files}

    @property
    def files(self):
        return self._files

    def __hash__(self):
        return hash(self._files)

    def __eq__(self, other):
        if not isinstance(other, LatexProject):
            return False
        return len(set(self._files.items()) - set(other._files.items())) == 0

    def setup(self, file_system, anchor):
        for (path, file) in self.files.items():
            location = anchor / path
            file_system.create_file(location, file.content)

    def assert_is_equivalent_to(self, other):
        self._verify_missing_files(other)
        self._verify_extraneous_files(other)
        self._verify_different_files(other)

    def _verify_different_files(self, other):
        for (path, file) in self.files.items():
            assert path in other.files and file == other.files[path], \
                self.CONTENT_MISMATCH.format(file=path, expected=file.content, actual=other.files[path].content)

    CONTENT_MISMATCH = "Content mismatch for {file}\nExpected:\n'{expected}'\nbut found:\n'{actual}'"

    def _verify_missing_files(self, other):
        for path in self.files:
            assert path in other.files, self.MISSING_FILE.format(file=path)

    MISSING_FILE = "Missing file '{file}'!"

    def _verify_extraneous_files(self, other):
        for path in other.files:
            assert path in self.files, self.UNEXPECTED_FILE.format(file=path)

    UNEXPECTED_FILE = "Unexpected file '{file}'!"


class LatexProjectBuilder:

    def __init__(self):
        self._files = []

    def build(self):
        return LatexProject(*self._files)

    def with_main_file(self, content):
        self._files.append(TexFile(self.MAIN_FILE, content))
        return self

    MAIN_FILE = "main.tex"

    def with_merged_file(self, content):
        self._files.append(TexFile(self.MERGED_FILE, content))
        return self

    MERGED_FILE = "merged.tex"

    def with_file(self, path, content):
        self._files.append(TexFile(path, content))
        return self

    def with_image(self, path):
        self._files.append(TexFile(path, self.IMAGE_CONTENT.format(key=path.replace("/", "_"))))
        return self

    IMAGE_CONTENT = "IMAGE DATA FOR {key}"


class TexFile:

    def __init__(self, name, content):
        self._name = name
        self._content = content

    @property
    def path(self):
        return self._name

    @property
    def content(self):
        return self._content

    def __eq__(self, other):
        if not isinstance(other, TexFile):
            return False
        return self._name == other._name and self._content == other._content

    def __hash__(self):
        return hash((self._name, self._content))


def a_project():
    return LatexProjectBuilder()


class Fragment:

    KEY_FILE = "file"
    KEY_LINE = "line"
    KEY_COLUMN = "column"
    KEY_CODE = "code"

    def __init__(self, file_name, line, column, code):
        self._file_name = file_name
        self._line = line
        self._column = column
        self._code = code

    @property
    def as_dictionary(self):
        return {self.KEY_FILE: self._file_name,
                self.KEY_LINE: self._line,
                self.KEY_COLUMN: self._column,
                self.KEY_CODE: self._code}


class FlapTestCase:

    def __init__(self, name, project, expected, skipped=False):
        if not len or len(name) == 0:
            raise ValueError("Invalid test case name (found '%s')" % name)
        self._name = name
        self._project = project
        self._expected = expected
        self._is_skipped = skipped

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        return self._project

    @property
    def expected(self):
        return self._expected

    @property
    def is_skipped(self):
        return self._is_skipped

    def run_with(self, runner):
        runner.test(self._name, self._project, self._expected)

    def __eq__(self, other):
        if not isinstance(other, FlapTestCase):
            return False
        return self._name == other._name and \
               self._project == other._project and \
               self._expected == other._expected and \
               self._is_skipped == other._is_skipped