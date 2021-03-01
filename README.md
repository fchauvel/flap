# FLaP &mdash; Flat LaTeX Projects

[![last release on PyPI](https://img.shields.io/pypi/v/FLaP.svg)](https://pypi.python.org/pypi/FLaP)
[![License](https://img.shields.io/pypi/l/FLaP.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Build status](https://img.shields.io/github/workflow/status/fchauvel/flap/run-test)](https://github.com/fchauvel/flap/actions)
[![Code coverage](https://img.shields.io/codecov/c/github/fchauvel/flap/master.svg)](https://codecov.io/gh/fchauvel/flap)
[![Code quality](https://img.shields.io/codacy/grade/df4826670c71444ca487434d612e96d7.svg)](https://www.codacy.com/app/fchauvel/flap/dashboard)
[![Downloads](https://img.shields.io/pypi/dm/FLaP.svg)](http://pypi-ranking.info/module/FLaP)

FlaP is a simple utility that flattens LaTeX projects. It takes a
well-organised LaTeX project&mdash;one you so carefully crafted&mdash;and
merged it into a vulgar single LaTeX file in a 'flat' directory.

  - *Why?* Some publishers require one such flat structure when you
    submit the sources of your manuscript, and I got tired to flatten
    the sources by hand.

  - *Another one?* There already a couple of tools that merge latex
    projects such as [latexpand](http://www.ctan.org/pkg/latexpand),
    [flatex](http://www.ctan.org/pkg/flatex) or
    [flatten](http://www.ctan.org/pkg/flatten). As far as I know, they
    only merge TeX files, without moving graphics around. I learned
    recently about
    [texDirflatten](http://www.ctan.org/pkg/texdirflatten), which
    seems to be an alternative, but I haven't tried it.

## Installation 

FLaP *requires* Python 3 (3.6, 3.6, 3.8 and 3.9 are tested). The easiest way to install latest
official release is to use pip using: 
```shell-session
$ pip install flap
```

Alternatively, you get the latest development version using:
```shell-session
$ pip install git+https://github.com/fchauvel/flap.git
```

Should you want to look at the code, you may download the sources
distribution and use 
```shell-session
$ git clone https://github.com/fchauvel/flap.git 
$ cd flap
$ python setup.py install .`
```

## Usage Example
For the newest (development) version, use:
 
```shell-session
$ flap project/main.tex output/directory
```

Prior to v0.4.1 (included), we invoke FLaP using:
```shell-session
$ python -m flap project/main.tex output/directory
```

See also the [online documentation](http://fchauvel.github.io/flap/index.html).

# Contact Us

If you give FLaP a try, please report any bugs, issues or feature request using the [issue tracker](https://github.com/fchauvel/flap/issues).


