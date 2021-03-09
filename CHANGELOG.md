# Versions History

## Next Release (under development)

 * Bug Fix:
   
   * Processing LaTeX commands where file names are quoted or include
     spaces, as per [Issue
     33](https://github.com/fchauvel/flap/issues/33)
    
   * Processing multiple fill that start with the same prefix, for
     instance myfile1.txt and myfile2.txt
     
 * Documentation
 
   * Different versions of the documentation are now accessible
     directly from Github.


## FLaP v0.6.0 (Mar. 7, 2021)

* New Features:
  * Support for [biblatex](https://ctan.org/pkg/biblatex?lang=en) and
    the `\addbibresource` command. Fix for [Issue
    #34](https://github.com/fchauvel/flap/issues/34)

* Documentation:
  * New layout powered by [Docute](https://docute.org/).
  * Now hosted by [Github
    Pages](http://fchauvel.github.io/flap/index.html)

* Dependencies
  * FLaP:
    * PyYAML 5.1 to 5.4.1
    * click 6.6 to 7.1.2
    * enum34 1.1.6 to 1.1.10
  * Developments:
    * green 2.15.0 to 3.2.5
    * coverage 4.2 to 5.5
    * mock 1.3.0 to 4.0.3
    * mkdocs 0.14 (deleted)

* Python versions:
    * Discard Python 3.3, 3.4 and 3.5 which are now deprecated
    * Add support for 3.7, 3.8 and 3.9
    
* Development Environment
  * CI moved from [Codeship](www.codeship.io) to Github Actions
  * Release from the CI, when the master branch is tagged

## FLaP v0.5.0 (Jan. 10, 2017)
This new version is a complete rewrite of the engine. FLaP now parses
the LaTeX sources instead of matching regular expressions. Among other
things, this permits a proper handling of verbatim environments. Any
feedback is more than welcome.

* Python Support:
    * FLaP v0.5.0 is not compatible with Python 3.2 any-more (now
      deprecated).
    * Support for Python 3.5 and 3.6

* New features:
    * Invocation using `flap main.tex output_dir` instead of `python
      -m flap ...`
    * A more robust command line interface, based on
      [Click](http://click.pocoo.org/6/)
    * Support for verbatim environments (e.g., `\begin{verbatim}`)
    * Generation of a log file to track what FLaP did (especially
      useful when it fails)
    * Detection of index files
    * Detection of bibliography files in subdirectories
    * Detection of required class files (e.g.,
      `\documentclass{my-arcticle}`)
    * Detection of required local packages (e.g.,
      `\usepackage{my-style}`)

* Documentation
    * Acceptance tests framework
    * Compatibility with Python version


## FLaP v0.4.1 (Oct. 3, 2016)

This new release fixes minor bugs, especially use of additional white
spaces in LaTeX commands. It also fixes:

 * Fix for running FLaP on a LaTeX file located in the working
   directory;
 * Fix regarding the extraction of subfiles directives;
 * Fix regarding whitspaces in multiline commands;
 * Fix extra space before the argument (including `\input`, `\include` ,
   `\includegraphics`, `\subfile`)

Besides, it also includes additional tools to describe end-to-end test
as YAML files, which can then be added without editing any code.

## FLaP v0.4.0 (Sep. 5, 2016)
This new version supports the use of the [subfiles
package](https://www.ctan.org/pkg/subfiles?lang=en) and also fixes
various bugs as follow:

 * Support invoking FLaP while giving a specific name to the merged
   file, using `python -m flap my/root.tex output/new_root.tex`
 * Fix flattening `\bibliography`stored in a subdirectory
 * Fix bug on `\graphicpath` directives using double curly braces
   (e.g., `\graphicpath{{./img/}}`).
 * Fix bugs on `\input` directives:
 * `\input` directive that specify the `.tex` extension are properly
   handled;
 * Relative paths specified in `\input` are considered from the root
   directory of the latex project, as LaTeX does.
 * Fix for LaTeX commands broken down over multiple lines (see Issue
   #12)
 * Fix for images whose name conflict once merged (see Issue #14)
 * Add support for `subfile` directives (see Issue #13)

## FLaP v0.3.0 (Sep. 16, 2015)

This new release now supports both `\includeonly`and
`\graphicspath`commands. It also includes a couple of bug fixes,
especially regarding the verbose option, which gets broken in v0.2.4
(see issue #8)

## FLaP v0.2.4 (Sep. 2, 2015)

Bug fix for Issue #1 and other minor improvements, such as support for
Python 3.3 and support for the `\endinput`command in Beamer
presentations.

## FLaP v0.2.3 (Aug. 27, 2015)

Bug fix regarding the resolution of included images paths
(https://github.com/fchauvel/flap/issues/3#issuecomment-136085551). In
addition, releases are now also tested under Python 3.2.

## FLaP v0.2.2 (Aug. 25, 2015)

Fix bugs reported in Issue
https://github.com/fchauvel/flap/issues/1#issuecomment-134835901 and
adding support for 'overpic' environment (see #2).

## FLaP v0.2.0 (Aug. 23, 2015)

Fix for Issue #1. This new release supports `\include` and
`\includesvg`directives as well as multi-line commands (where a LaTeX
command is broken down using comments).

## FLaP v0.1.0 (Aug. 15, 2015)

First release! Three main things:
 * Only detect `\includegraphics` and `\input`directives
 * Not yet tested under a UNIX-like file system
 * Does not support "relative path" such as `../my/thing`
