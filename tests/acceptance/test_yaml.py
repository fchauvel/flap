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

from unittest import TestCase

from io import StringIO
from flap.ui import UI
from flap.util.oofs import InMemoryFileSystem
from flap.util.path import Path, TEMP
from mock import MagicMock
from tests.commons import AcceptanceTestRunner
from tests.latex_project import Fragment, LatexProject, TexFile, a_project, FlapTestCase
from tests.acceptance.yaml import FileBasedTestRepository, YamlCodec, InvalidYamlTestCase


class FlapTestCaseTests(TestCase):

    def setUp(self):
        self.project = a_project().with_main_file("blabla").build()
        self.expected = a_project().with_merged_file("blabla").build()
        self.test_case_name = "foo"
        self.output = [Fragment("test.tex", 1, 1, r"\input{foo}")]
        self.test_case = FlapTestCase(self.test_case_name, self.project, self.expected, False, self.output)

    def test_is_not_skipped(self):
        self.assertFalse(self.test_case.is_skipped)

    def test_name_is_exposed(self):
        self.assertEqual(self.test_case_name, self.test_case.name)

    def test_reject_empty_names(self):
        with self.assertRaises(ValueError):
            FlapTestCase("", self.project, self.expected)

    def test_project_is_exposed(self):
        self.assertIs(self.project, self.test_case.project)

    def test_expectation_is_exposed(self):
        self.assertIs(self.expected, self.test_case.expected)

    def test_equals_itself(self):
        self.assertEquals(self.test_case, self.test_case)

    def test_equals_a_similar_test_case(self):
        self.assertEqual(
            FlapTestCase(
                "foo",
                a_project().with_main_file("blabla").build(),
                a_project().with_merged_file("blabla").build(),
                False,
                [Fragment("test.tex", 1, 1, r"\input{foo}")]),
            self.test_case)

    def test_differs_from_a_project_with_another_expectation(self):
        self.assertNotEqual(
            FlapTestCase(
                "foo",
                a_project().with_main_file("blabla").build(),
                a_project().with_merged_file("something different").build(),
                False,
                [Fragment("test.tex", 1, 1, r"\input{foo}")]),
            self.test_case)

    def test_differs_from_an_equivalent_but_skipped_case(self):
        self.assertNotEqual(
            FlapTestCase(
                "foo",
                a_project().with_main_file("blabla").build(),
                a_project().with_merged_file("blabla").build(),
                True,
                [Fragment("test.tex", 1, 1, r"\input{foo}")]),
            self.test_case)

    def test_differs_from_an_equivalent_but_with_different_output(self):
        self.assertNotEqual(
            FlapTestCase(
                "foo",
                a_project().with_main_file("blabla").build(),
                a_project().with_merged_file("blabla").build(),
                output=[Fragment("test.tex", 123, 0, r"\input{foo}")]),
            self.test_case)

    def test_test_with(self):
        runner = MagicMock()
        self.test_case.run_with(runner)
        runner.test.assert_called_once_with(self.test_case.name, self.test_case._project, self.test_case._expected)


class TestSkippedFlapTestCase(TestCase):

    def setUp(self):
        self.project = a_project().with_main_file("blabla").build()
        self.expected = a_project().with_merged_file("blabla").build()
        self.test_case_name = "foo"
        self.test_case = FlapTestCase(self.test_case_name, self.project, self.expected, True)

    def test_is_skipped(self):
        self.assertTrue(self.test_case.is_skipped)


class TestYamlCodec(TestCase):

    def setUp(self):
        self._codec = YamlCodec()

    def _create_file(self, content):
        file = MagicMock()
        file.content.return_value = content
        return file

    def test_loading_test_case_with_latex_code(self):
        yaml_file = self._create_file(YamlTest.with_latex_code())

        test_case = self._read_test_case_from(yaml_file)

        expected = FlapTestCase(
                        "test 1",
                        a_project().with_main_file("\\documentclass{article}\n\\begin{document}\n  This is a simple \\LaTeX document!\n\\end{document}").build(),
                        a_project().with_merged_file("\\documentclass{article}\n\\begin{document}\n  This is a simple \\LaTeX document!\n\\end{document}").build())

        self.assertEqual(expected, test_case)

    def test_parsing_a_skipped_yaml_code(self):
        yaml_file = self._create_file(YamlTest.that_is_skipped("Test 1"))
        test_case = self._read_test_case_from(yaml_file)

        expected = FlapTestCase(
                        "Test 1",
                        a_project().with_main_file("blabla").build(),
                        a_project().with_merged_file("blabla").build(),
                        True)

        self.assertEqual(expected, test_case)

    def test_parsing_a_test_case_with_expected_outputs(self):
        yaml_file = self._create_file(YamlTest.that_includes_expected_outputs("Test 1"))
        test_case = self._read_test_case_from(yaml_file)

        expected = FlapTestCase(
                        "Test 1",
                        a_project().with_main_file("blabla").build(),
                        a_project().with_merged_file("blabla").build(),
                        False,
                        [Fragment("main.tex", 1, 1, "\\input{result}")])

        self.assertEqual(expected, test_case)

    def test_parsing_invalid_yaml_code(self):
        yaml_file = self._create_file("This is not a valid YAML content!")
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_project_key(self):
        yaml_file = self._create_file(YamlTest.with_misspelled_project_key())
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_name_key(self):
        yaml_file = self._create_file(YamlTest.with_misspelled_name_key())
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_path_key(self):
        yaml_file = self._create_file(YamlTest.with_misspelled_path_key())
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_content_key(self):
        yaml_file = self._create_file(YamlTest.with_misspelled_content_key())
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_expected_key(self):
        yaml_file = self._create_file(YamlTest.with_misspelled_expected_key())
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def _read_test_case_from(self, file):
        return self._codec.extract_from(file)


class TestRepositoryTest(TestCase):

    def setUp(self):
        self.file_system = InMemoryFileSystem()
        self.repository = FileBasedTestRepository(
            self.file_system,
            Path.fromText("tests"),
            YamlCodec())

    def test_do_not_found_test_that_do_not_exist(self):
        test_cases = self._fetch_all_tests()
        self.assertEqual(0, len(test_cases))

    def test_found_one_test_if_only_one_yml_exists(self):
        self._create_file("tests/test.yml", YamlTest.with_latex_code())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_found_one_test_if_only_one_yaml_exists(self):
        self._create_file("tests/test.yaml", YamlTest.with_latex_code())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_ignore_files_that_are_not_yaml(self):
        self._create_file("tests/test.txt", YamlTest.with_latex_code())
        test_cases = self._fetch_all_tests()
        self.assertEqual(0, len(test_cases))

    def test_spot_files_hidden_in_sub_directories(self):
        self._create_file("tests/sub_dir/test_2.yml", YamlTest.with_latex_code())
        test_cases = self._fetch_all_tests()
        self._verify(test_cases)

    def _verify(self, test_cases):
        self.assertEqual(1, len(test_cases))
        expected = FlapTestCase(
            "test 1",
            a_project().with_main_file(self.LATEX_CODE).build(),
            a_project().with_merged_file(self.LATEX_CODE).build())
        self.assertEqual(expected, test_cases[0])

    LATEX_CODE = ("\\documentclass{article}\n"
                  "\\begin{document}\n"
                  "  This is a simple \\LaTeX document!\n"
                  "\\end{document}")

    def _fetch_all_tests(self):
        return self.repository.fetch_all()

    def _create_file(self, path, content):
        self.file_system.create_file(Path.fromText(path), content)


class TestRunningTestCase(TestCase):

    def setUp(self):
        self._directory = TEMP / "flap"
        self._project_path = self._directory / "test_1" / "project"
        self._root_tex_file = self._project_path / "main.tex"
        self._output_path = self._directory / "test_1" / "flatten"
        self._file_system = InMemoryFileSystem()
        self._test_case = None
        self._display = StringIO()
        self._runner = AcceptanceTestRunner(self._file_system, self._directory, UI(self._display))

    def _run_test(self):
        assert self._test_case is not None
        self._test_case.run_with(self._runner)

    def test_running_a_test_case_that_passes(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla")))

        try:
            self._run_test()

        except Exception as e:
            self.fail("Unexpected exception " + str(e))

    def test_running_a_test_case_that_fails(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla blabla")))

        with self.assertRaises(AssertionError):
            self._run_test()

    def test_running_a_test_case_that_throws_an_exception(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla")))

        self._runner._run_flap = MagicMock()
        self._runner._run_flap.side_effect = Exception()

        with self.assertRaises(Exception):
            self._run_test()


class YamlTest:

    @staticmethod
    def that_is_invalid():
        return "blabla bla"

    @staticmethod
    def that_is_skipped(test_name):
        return ("name: {name}\n"
                "skipped: true\n"
                "project:\n"
                " - path: main.tex\n"
                "   content: blabla\n"
                "expected:\n"
                "  - path: merged.tex\n"
                "    content: blabla\n").format(name=test_name)

    @staticmethod
    def with_misspelled_project_key():
        return ("name: test 1\n"
                "projecttttttttt:\n"
                "  - path: main.tex\n"
                "    content: |\n"
                "      \\begin{document}Awesone!\\end{document}\n")

    @staticmethod
    def with_misspelled_name_key():
        return ("nameeeeeeeeeeeeeeeee: test 1\n")

    @staticmethod
    def with_misspelled_path_key():
        return ("name: test 1\n"
                "project:\n"
                "  - pathhhhhhhhh: main.tex\n"
                "    content: |\n"
                "      \\begin{document}Awesone!\\end{document}\n")

    @staticmethod
    def with_misspelled_expected_key():
        return ("name: test 1\n"
                "project:\n"
                "  - path: main.tex\n"
                "    content: |\n"
                "      \\begin{document}Awesone!\\end{document}\n"
                "expectedddddddddd:\n")

    @staticmethod
    def with_misspelled_content_key():
        return ("name: test 1\n"
                "project:\n"
                "  - path: main.tex\n"
                "    contentttttttttttt: |\n"
                "      \\begin{document}Awesone!\\end{document}\n")

    @staticmethod
    def with_latex_code():
        return ( "name: test 1 \n"
                 "description: >\n"
                 "  This is a dummy test, for testing purposes\n"
                 "project:\n"
                 "  - path: main.tex\n"
                 "    content: |\n"
                 "      \\documentclass{article}\n"
                 "      \\begin{document}\n"
                 "        This is a simple \\LaTeX document!\n"
                 "      \\end{document}\n"
                 "expected:\n"
                 "  - path: merged.tex\n"
                 "    content: |\n"
                 "      \\documentclass{article}\n"
                 "      \\begin{document}\n"
                 "        This is a simple \\LaTeX document!\n"
                 "      \\end{document}\n")

    @staticmethod
    def that_includes_expected_outputs(name):
         return ("name: {name}\n".format(name=name) +
                 "project:\n"
                 " - path: main.tex\n"
                 "   content: blabla\n"
                 "expected:\n"
                 "  - path: merged.tex\n"
                 "    content: blabla\n"
                 "outputs:\n"
                 "  - file: main.tex\n"
                 "    line: 1\n"
                 "    column: 1\n"
                 "    code: \\input{result}\n")

    @staticmethod
    def that_passes(test_case_name):
        return ("name: {name}\n"
                "project:\n"
                " - path: main.tex\n"
                "   content: blabla\n"
                "expected:\n"
                "  - path: merged.tex\n"
                "    content: blabla\n").format(name=test_case_name)

    @staticmethod
    def that_fails_because_of_missing_file(test_name):
        return ("name: {name}\n"
                "project:\n"
                " - path: main.tex\n"
                "   content: blabla\n"
                "expected:\n"
                "  - path: not_merged.tex\n"
                "    content: new blabla\n").format(name=test_name)

    @staticmethod
    def that_fails_because_of_content_mismatch(test_name):
        return ("name: {name}\n"
                "project:\n"
                " - path: main.tex\n"
                "   content: blabla\n"
                "expected:\n"
                "  - path: merged.tex\n"
                "    content: something not expected!\n").format(name=test_name)

    @staticmethod
    def that_fails_because_of_unexpected_file(test_name):
        return ("name: {name}\n"
                "project:\n"
                " - path: main.tex\n"
                "   content: blabla\n"
                "expected:\n"
                "  - path: rewritten.tex\n"
                "    content: blabla\n").format(name=test_name)


