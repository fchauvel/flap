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
from mock import MagicMock

from flap.FileSystem import InMemoryFileSystem
from flap.path import Path
from tests.acceptance.latex_project import TexFile, LatexProject
from tests.acceptance.engine import FlapTestCase, FileBasedTestRepository, YamlCodec, \
    InvalidYamlTestCase, TestRunner, Verdict


class FlapTestCaseTests(TestCase):

    def setUp(self):
        self.project = LatexProject(TexFile("main.tex", "blabla"))
        self.expected = LatexProject(TexFile("main.tex", "blabla"))
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

    def test_equals_itself(self):
        self.assertEquals(self.test_case, self.test_case)

    def test_equals_a_similar_test_case(self):
        self.assertEqual(FlapTestCase(
            "foo",
            LatexProject(TexFile("main.tex", "blabla")),
            LatexProject(TexFile("main.tex", "blabla"))
        ),
        self.test_case)

    def test_differs_from_a_project_with_another_expectation(self):
        self.assertNotEqual(FlapTestCase(
            "foo",
            LatexProject(TexFile("main.tex", "blabla")),
            LatexProject(TexFile("main.tex", "something different"))
        ),
        self.test_case)

    def test_preparation_on_file_system(self):
        file_system = InMemoryFileSystem()

        self.test_case.setup(file_system)

        file = file_system.open(Path.fromText("main.tex"))
        self.assertIsNotNone(file)
        self.assertEqual("blabla", file.content())


class TestLatexProjectSetup(TestCase):

    def setUp(self):
        self.file_system = InMemoryFileSystem()
        self.project = LatexProject(TexFile("main.tex", "blabla"))

    def _setup(self):
        self.project.setup(self.file_system)

    def test_setup_of_simple_project(self):
        self.project = LatexProject(TexFile("main.tex", "blabla"))

        self._setup()

        file = self.file_system.open(Path.fromText("main.tex"))
        self.assertIsNotNone(file)
        self.assertEqual("blabla", file.content())

    def test_setup_of_project_with_subdirectories(self):
        self.project = LatexProject(TexFile("main.tex", "blabla"))

        self._setup()

        file = self.file_system.open(Path.fromText("main.tex"))
        self.assertIsNotNone(file)
        self.assertEqual("blabla", file.content())



class TestYamlCodec(TestCase):

    def setUp(self):
        self._codec = YamlCodec()

    def test_loading_a_simple_yaml_test_case(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "project:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      blabla\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      blabla\n")

        test_case = self._read_test_case_from(yaml_file)

        expected = FlapTestCase(
                        "test 1",
                        LatexProject(TexFile("main.tex", "blabla")),
                        LatexProject(TexFile("main.tex", "blabla")))

        self.assertEqual(expected, test_case)

    def _create_file(self, content):
        file = MagicMock()
        file.content.return_value = content
        return file

    def test_loading_test_case_with_latex_code(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "project:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")

        test_case = self._read_test_case_from(yaml_file)

        expected = FlapTestCase(
                        "test 1",
                        LatexProject(TexFile("main.tex", "\\begin{document}Awesone!\\end{document}")),
                        LatexProject(TexFile("main.tex", "\\begin{document}Awesone!\\end{document}")))

        self.assertEqual(expected, test_case)

    def test_parsing_invalid_yaml_code(self):
        yaml_file = self._create_file("This is not a valid YAML content!")
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_project_key(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "projecttttttttt:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")

        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_name_key(self):
        yaml_file = self._create_file("nameeeeeeeeeeeeeeeee: test 1\n"
                                      "project:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_path_key(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "project:\n"
                                      "  - pathhhhhhhhh: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_content_key(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "project:\n"
                                      "  - path: main.tex\n"
                                      "    contentttttttttttt: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expected:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")
        with self.assertRaises(InvalidYamlTestCase):
            self._read_test_case_from(yaml_file)

    def test_wrong_expected_key(self):
        yaml_file = self._create_file("name: test 1\n"
                                      "project:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n"
                                      "expectedddddddddd:\n"
                                      "  - path: main.tex\n"
                                      "    content: |\n"
                                      "      \\begin{document}Awesone!\\end{document}\n")
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
        self._create_file("tests/test.yml", self._dummy_yaml_test_case())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_found_one_test_if_only_one_yaml_exists(self):
        self._create_file("tests/test.yaml", self._dummy_yaml_test_case())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_ignore_files_that_are_not_yaml(self):
        self._create_file("tests/test.txt", self._dummy_yaml_test_case())
        test_cases = self._fetch_all_tests()
        self.assertEqual(0, len(test_cases))

    def test_spot_files_hidden_in_sub_directories(self):
        self._create_file("tests/sub_dir/test_2.yml", self._dummy_yaml_test_case())
        test_cases = self._fetch_all_tests()
        self._verify(test_cases)

    def _verify(self, test_cases):
        self.assertEqual(1, len(test_cases))
        expected = FlapTestCase(
            "test 1",
            LatexProject(TexFile("main.tex", ("\\documentclass{article}\n"
                                               "\\begin{document}\n"
                                               "  This is a simple \\LaTeX document!\n"
                                               "\\end{document}"))),
            LatexProject(TexFile("main.tex", ("\\documentclass{article}\n"
                                               "\\begin{document}\n"
                                               "  This is a simple \\LaTeX document!\n"
                                               "\\end{document}")))
        )
        self.assertEqual(expected, test_cases[0])

    def _dummy_yaml_test_case(self):
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
                 "  - path: main.tex\n"
                 "    content: |\n"
                 "      \\documentclass{article}\n"
                 "      \\begin{document}\n"
                 "        This is a simple \\LaTeX document!\n"
                 "      \\end{document}\n")

    def _fetch_all_tests(self):
        return self.repository.fetch_all()

    def _create_file(self, path, content):
        self.file_system.create_file(Path.fromText(path), content)


class TestTestRunner(TestCase):

    def setUp(self):
        self.test_case = MagicMock()
        self.runner = None

    def _run_tests(self, tests):
        self.runner = TestRunner(tests)
        return self.runner.run()

    def test_running_a_test_that_passes(self):
        self.test_case.run.return_value = Verdict.PASS

        results = self._run_tests([self.test_case])

        self.assertEqual([(self.test_case, Verdict.PASS)], results)

    def test_running_two_tests(self):
        self.test_case.run.side_effect = [Verdict.PASS, Verdict.FAILED]

        results = self._run_tests([self.test_case, self.test_case])

        self.assertEqual(
            [(self.test_case, Verdict.PASS),
             (self.test_case, Verdict.FAILED)],
            results)

    def test_running_a_sequence_where_one_test_fails_midway(self):
        self.test_case.run.side_effect = [
            Verdict.PASS,
            Exception("Unknown Error"),
            Verdict.FAILED]

        results = self._run_tests([self.test_case, self.test_case, self.test_case])

        self.assertEqual(
            [(self.test_case, Verdict.PASS),
             (self.test_case, Verdict.ERROR),
             (self.test_case, Verdict.FAILED)],
            results)

    def test_running_a_test_that_raise_an_exception(self):
        self.test_case.run.side_effect = Exception("Unknown Error")

        results = self._run_tests([self.test_case])

        self.assertEqual([(self.test_case, Verdict.ERROR)], results)


