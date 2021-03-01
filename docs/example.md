# Usage Example

## A Dummy LaTeX Project

Let's consider the sample LaTeX project, whose source is broken in broken down into several TeX files. The `project/main.tex` contains the overall structure of the document, whereas separate
LaTeX files each contains a section. In addition, the `project/img` directory contains the graphic files to be included, 
for instance `img/screenshot.pdf`. The tree-structure of the project directory follows:

```shell-session
$ tree
    /home/me/project/
       ├ main.tex
       ├ part1.tex
       └ img/
         └ screenshot.pdf
```

The main LaTeX document `project/main.tex` contains the following code:

```latex
\documentclass{article}

\begin{document}
    \input{part1}
\end{document}
```

The second LaTeX file `project/part1.tex` contains an graphic inclusion directive as follows:
```latex
Here is some additional text, and a graphics.

\begin{center}
    \includegraphics[width=\textwidth]{img/screenshot}
\end{center}

Followed by some explanation about what to see on this screenshot.
```

## Running FLaP
FLaP can merge this LaTeX project into a single LaTeX file, and adjusts the graphics inclusion directives.
To do so, we invoke FLaP as follows:
  
```shell-session
$ cd /home/me
$ flap project/main.tex output_dir
```

> Prior to version 0.5, FLaP was invoked using `python3 -m flap main.tex output_dir`

> Prior to version 0.2.3, FLaP was invoked using `python3 -m flap.ui main.tex output_dir`.

> You may as well use the "verbose" option (`-v`) to get more details about what FLaP is doing.

## Checking out the Results
The above command creates a directory `output_dir`, with the following project structure:

    /home/me
     ├ project/
     │  ├ main.tex
     │  ├ part1.tex
     │  └ img/
     │     └ screenshot.pdf
     └ output_dir/
       ├ merged.tex
       └ screenshot.pdf

where the LaTeX code resulting from the merge is:

```tex
\documentclass{article}

\begin{document}
    Here is some additional text, and a graphics.

\begin{center}
    \includegraphics[width=\textwidth]{screenshot}
\end{center}

Followed by some explanation about what to see on this screenshot.
\end{document}
```
