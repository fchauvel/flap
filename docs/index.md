# FLaP &mdash; Flat LaTeX Projects

![Version on Pypi](https://img.shields.io/pypi/v/FLaP.svg)
![license](https://img.shields.io/pypi/l/FLaP.svg)
![build](https://img.shields.io/codeship/ad32e1e0-27d8-0133-8e78-7af7072ae828.svg)
![code coverage](https://img.shields.io/codecov/c/github/fchauvel/flap/master.svg)
![downloads](https://img.shields.io/pypi/dm/FLaP.svg)

FlaP is an utility that flattens LaTeX projects. It takes a well organised LaTeX project 
&mdash; one you carefully crafted &mdash; and merged it into a single LaTeX file 
in a flat directory.

 * __Why?__ 
   Some publishers require such a flat structure when you submit the sources of your 
   manuscripts, and I got tired to flatten the sources by hand.

 * __Yet Another One?__ 
   There is already a couple of tools that merge latex projects such as [latexpand](http://www.ctan.org/pkg/latexpand),
   [flatex](http://www.ctan.org/pkg/flatex) or [flatten](http://www.ctan.org/pkg/flatten). As far as I know, they only merge
   TeX files, without moving graphics around. I learned recently about
   [texdirflatten](http://www.ctan.org/pkg/texdirflatten), which seems to be an alternative, but I haven't tried it.

## Install

	$> pip install flap

## Use

	$> python3 -m flap my/project/main.tex my/output
	
## Doesn't work?

If you  give it a try, please report any bugs, issues, feature request or missing documentation using 
the [issue tracker](https://github.com/fchauvel/flap/issues).
Should you need any further information, feel free to email [me](mailto:franck.chauvel@gmail.com)