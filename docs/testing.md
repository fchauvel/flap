# Testing

## Unit Tests

FLaP comes along with a test suite that helps find bugs, regressions especially. To run the test suite, type:

    $> python setup.py test

Alternatively, you can use [Tox](https://testrun.org/tox/latest/) to test over several Python platform. The current 
configuration (see file `tox.ini`) will run the test suite using Python 3.2, 3.3 and 3.4.

    $> tox          # Test all platforms
    $> tox -e py32  # To test a specific platform

## Acceptance Tests

FLaP also includes a few "acceptance tests" that check various types of 
LaTeX projects. Theses acceptance tests are end-to-end tests that trigger
FLaP from the outset.

Each acceptance test in described in a separate YAML file, as shown in 
the example below, where we describe a single-file project and the content
expected once it is flattened.

```yaml
# Some metadata about the test
name: nothing_to_flatten
description: >
  Test that FLaP does not change anything in projects where nothing
  needs to be flatten
  
# Describe the LaTeX project to flatten
project:
  - path: main.tex
    content: |
      \documentclass{article}
      \begin{document}
      This is a simple LaTeX document!
      \end{document}

# Describe the expected flattened LaTeX project
expected:
  - path: merged.tex
    content: |
      \documentclass{article}
      \begin{document}
      This is a simple LaTeX document!
      \end{document}
```

By convention, such LaTeX project must have their root file named `main.tex`, at
its top level. Similarly, FLaP will be invoked with its default options,
and will therefore generate a file named `merged.tex`.

By convention, the acceptance tests are located in `tests/acceptance/tests`
and we can organise them into subdirectories as need be. 

All the YAML tests are automatically detected and bundled into a single Python class `YAMLAcceptanceTests` ( 
dynamically generated&mdash;don't search for it). We can use unittest to run only these acceptance tests using:
````bash
$ python -m unittest -v tests.acceptance
test Bibliography in a sub-directory (tests.acceptance.YAMLTests) ... ok
test Nothing to flatten (tests.acceptance.YAMLTests) ... ok
test \includegraphics without extension (tests.acceptance.YAMLTests) ... ok
test \input used recursively (tests.acceptance.YAMLTests) ... ok
test \input without extension (tests.acceptance.YAMLTests) ... ok
test conflicting \includegraphics (tests.acceptance.YAMLTests) ... ok
test graphicspath (tests.acceptance.YAMLTests) ... ok
test include directive (tests.acceptance.YAMLTests) ... ok
test include only directive (tests.acceptance.YAMLTests) ... ok
test multiline commands (tests.acceptance.YAMLTests) ... ok
test subfiles from the subfiles package (tests.acceptance.YAMLTests) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.076s

OK
````

> Note that these acceptance tests are first deserialised on disk in 
the `$TEMP/flap/acceptance`, where `$TEMP` for stands the temporary 
directory. The resulting directories are only deleted when these tests start, and looking at what was produced can help you troubleshoot.
You can check where `$TEMP` points using:
`$> python -c "import tempfile;print(tempfile.gettempdir())"`

