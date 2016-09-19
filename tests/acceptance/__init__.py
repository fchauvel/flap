

from unittest import TestCase


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


class LatexProject:

    def __init__(self, files):
        self._files = {each_file.path: each_file for each_file in files}

    @property
    def files(self):
        return self._files

    def __hash__(self):
        return hash(self._files)

    def __eq__(self, other):
        if not isinstance(other, LatexProject):
            return False
        return len(set(self._files) - set(other._files)) == 0


class FlapTestCase:

    def __init__(self, name, project, expected):
        if not len or len(name) == 0:
            raise ValueError("Invalid test case name (found '%s')" % name)
        self._name = name
        self._project = project
        self._expected = expected

    @property
    def name(self):
        return self._name

    @property
    def project(self):
        return self._project

    @property
    def expected(self):
        return self._expected


class TexFileTest(TestCase):

    def setUp(self):
        self.path = "test/main.tex"
        self.content = "foo"
        self.tex_file = TexFile(self.path, self.content)

    def test_name_is_exposed(self):
        self.assertEqual(self.path, self.tex_file.path)

    def test_content_is_exposed(self):
        self.assertEquals(self.content, self.tex_file.content)

    def test_equals_itself(self):
        self.assertEqual(self.tex_file, self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_path(self):
        self.assertNotEqual(TexFile("dir/" + self.path, self.content),
                            self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_content(self):
        self.assertNotEqual(TexFile(self.path, self.content + "blablabla"),
                            self.tex_file)


class LatexProjectTests(TestCase):

    def setUp(self):
        self.files = [ TexFile("main.tex", "blabla") ]
        self.tex = LatexProject(self.files)

    def test_files_is_exposed(self):
        self.assertEquals(self.files[0], self.tex.files["main.tex"])

    def test_equals_a_project_with_similar_files(self):
        self.assertEqual(LatexProject([TexFile("main.tex", "blabla")]),
                         self.tex)


class FlapTestCaseTests(TestCase):

    def setUp(self):
        self.project = LatexProject([TexFile("main.tex", "blabla")])
        self.expected = LatexProject([TexFile("main.tex", "blabla")])
        self.test_case_name = "foo"
        self.test_case = FlapTestCase(self.test_case_name, self.project, self.expected)

    def test_name_is_exposed(self):
        self.assertEqual(self.test_case_name, self.test_case.name)

    def test_reject_empty_names(self):
        with self.assertRaises(ValueError):
            FlapTestCase("", self.project, self.expected)

    def test_project_is_exposed(self):
        self.assertIs(self.project, self.test_case.project)

    def test_expectation_is_exposed(self):
        self.assertIs(self.expected, self.test_case.expected)
