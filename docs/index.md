# FLaP &mdash; Flat LaTeX Projects

![Version on Pypi](https://img.shields.io/pypi/v/FLaP.svg)
![license](https://img.shields.io/pypi/l/FLaP.svg)
![build](https://img.shields.io/codeship/ad32e1e0-27d8-0133-8e78-7af7072ae828.svg)
![code coverage](https://img.shields.io/codecov/c/github/fchauvel/flap/master.svg)
![code quality](https://img.shields.io/codacy/grade/df4826670c71444ca487434d612e96d7.svg)
![downloads](https://img.shields.io/pypi/dm/FLaP.svg)

FlaP is an utility that flattens LaTeX projects. It takes a well organised LaTeX 
project&mdash;one you carefully crafted&mdash;and merged it into a single LaTeX file 
in a flat directory. Images, bibliography and others resources are moved around as well.

 * __What does FLaP support?__ The [list of supported directives](features) includes most commonly 
 used LaTeX directives, such as `\input`, `\include`, `\includegraphics`, etc. Yet, FLaP does
 not support these directives when I we use them within verbatim environments or within 
 user-defined commands.
 
 * __Why?__ 
   Some publishers require such a flat structure when you submit the sources of your 
   manuscripts, and I got tired to flatten the sources by hand.

 * __Yet Another One?__ 
   There is already a couple of tools that merge LaTeX projects such as [latexpand](http://www.ctan.org/pkg/latexpand),
   [flatex](http://www.ctan.org/pkg/flatex), [flatten](http://www.ctan.org/pkg/flatten) or 
   [texdirflatten](http://www.ctan.org/pkg/texdirflatten). As far as I know, they do not support directives such as 
   `\graphicspath` and `\includeonly` and only merge TeX files, without moving graphics around (except for `texdirflatten`).

## Install

	$> pip install flap

## Use

	$> python3 -m flap my/project/main.tex my/output
	
## Contact Us

If you give FLaP a try, please report any bugs, issues or feature request using the
[issue tracker](https://github.com/fchauvel/flap/issues).

Feel free to share any question or comment on our [FLaP mailing list](mailto:flap-general@freelists.org). Note that you must
subscribe first by sending an email to 'flap-general-request@freelists.org' with 'subscribe' in the Subject field OR by
visiting [our subscription page](http://www.freelists.org/list/flap-general).