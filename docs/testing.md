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
LaTeX projects. Theses acceptance tests are also 
end-to-end tests that trigger FLaP from the outset, in a separate 
process. 

Each acceptance test in described in a separate YAML file, as shown in 
the example below:

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

By convention, each LaTeX project must have a file named `main.tex` at
its top level. Similarly, FLaP will be invoked with its default options,
and will therefore generate a file named `merged.tex`.