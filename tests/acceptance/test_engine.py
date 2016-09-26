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

from io import StringIO
from flap.FileSystem import InMemoryFileSystem
from flap.path import Path, TEMP
from tests.acceptance.latex_project import TexFile, LatexProject, MissingFile
from tests.acceptance.engine import FlapTestCase, FileBasedTestRepository, YamlCodec, \
    InvalidYamlTestCase, TestRunner, Verdict, Acceptor, FailedVerdict, ErrorVerdict, SuccessVerdict


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

    def test_run(self):
        runner = MagicMock()
        self.test_case.run_with(runner)
        runner.test.assert_called_once_with(self.test_case.name, self.test_case.project, self.test_case.expected)


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


class VerdictTests(TestCase):

    def setUp(self):
        self._test_case_name = "foo"
        self._verdict = None
        self._spy = MagicMock()

    def _traverse(self):
        assert self._verdict is not None, "The verdict has not been initialised!"
        self._verdict.accept(self._spy)

    def test_passed(self):
        self._verdict = Verdict.passed(self._test_case_name)
        self._traverse()
        self._spy.on_success.assert_called_once_with(self._test_case_name)

    def test_failed_expose_differences(self):
        differences = [MissingFile("main.tex")]
        self._verdict = Verdict.failed(self._test_case_name, differences)
        self._traverse()
        self._spy.on_failure.assert_called_once_with(self._test_case_name, differences)

    def test_error_expose_caught_exception(self):
        caught_exception = Exception("Unknown error")
        self._verdict = Verdict.error(self._test_case_name, caught_exception)
        self._traverse()
        self._spy.on_error.assert_called_once_with(self._test_case_name, caught_exception)


class TestRunningTestCase(TestCase):

    def setUp(self):
        self._directory = TEMP / "flap"
        self._project_path = self._directory / "test_1" / "project"
        self._root_tex_file = self._project_path / "main.tex"
        self._output_path = self._directory / "test_1" / "flatten"
        self._file_system = InMemoryFileSystem()
        self._test_case = None
        self._runner = TestRunner(self._file_system, self._directory)

    def _run_test(self):
        assert self._test_case is not None
        return self._test_case.run_with(self._runner)

    def test_running_a_test_case_that_passes(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla")))

        verdict = self._run_test()

        self.assertIsInstance(verdict, SuccessVerdict)

    def test_running_a_test_case_that_fails(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla blabla")))

        verdict = self._run_test()

        self.assertIsInstance(verdict, FailedVerdict)

    def test_running_a_test_case_that_throws_an_exception(self):
        self._test_case = FlapTestCase("test 1",
                                       LatexProject(TexFile("main.tex", "blabla")),
                                       LatexProject(TexFile("merged.tex", "blabla")))

        self._runner._run_flap = MagicMock()
        self._runner._run_flap.side_effect = Exception()

        verdict = self._run_test()

        self.assertIsInstance(verdict, ErrorVerdict)


class ControllerTest(TestCase):

    def setUp(self):
        self._file_system = InMemoryFileSystem()
        self._output = StringIO()

    def test_output_when_no_test_are_found(self):
        self._file_system.create_file(Path.fromText("tests/this_is_not_a_test.txt"), "blabla")

        self._check_acceptance()

        self.assertIn(Acceptor.NO_TEST_FOUND, self._output.getvalue())


    def test_output(self):
        self._file_system.create_file(Path.fromText("tests/test_1.yml"),
                                              "name: Test 1\n"
                                              "project:\n"
                                              " - path: main.tex\n"
                                              "   content: blabla\n"
                                              "expected:\n"
                                              "  - path: merged.tex\n"
                                              "    content: blabla\n")
        self._file_system.create_file(Path.fromText("tests/test_2.yml"),
                                              "name: Test 2\n"
                                              "project:\n"
                                              " - path: main.tex\n"
                                              "   content: blabla\n"
                                              "expected:\n"
                                              "  - path: merged.tex\n"
                                              "    content: new blabla\n")

        self._check_acceptance()

        self.assertIn(Acceptor.TEST_CASE.format(name="Test 1", verdict=Acceptor.TEST_PASS), self._output.getvalue())
        self.assertIn(Acceptor.TEST_CASE.format(name="Test 2", verdict=Acceptor.TEST_FAILED), self._output.getvalue())
        self.assertIn(Acceptor.HORIZONTAL_LINE, self._output.getvalue())
        self.assertIn(Acceptor.SUMMARY.format(total=2, passed=1, failed=1, error=0), self._output.getvalue())

    def _check_acceptance(self):
        repository = FileBasedTestRepository(self._file_system, Path.fromText("tests"), YamlCodec())
        runner = TestRunner(self._file_system, TEMP / "flap" / "acceptance")
        acceptance = Acceptor(repository, runner, self._output)
        acceptance.check()
