# Usage Example

## A Sample LaTeX Project

Let's consider the sample LaTeX project. One that is fairly well structured: the LaTeX code is  
broken down into several files. The `project/main.tex` contains the overall structure of the document, whereas separate 
LaTeX files each contains a section. In addition, the `project/img` directory contains the graphic files to be included, 
for instance `img/screenshot.pdf`.

	project/
		main.tex
		part1.tex
		img/
			screenshot.pdf

The main LaTeX document (`project/main.tex`), is very simple and contains the following code:

```tex
% Sample LaTeX document
\documentclass{article}

\begin{document}
	
    \input{part1}
	
\end{document}
```

The second LaTeX file (`project/part1.tex`) contains an inclusion directive as follows:
```tex
Here is some additional text, and a graphics.
\begin{center}
    \includegraphics[width=\textwidth]{img/screenshot}
\end{center}
Followed by some explanation about what to see on this screenshot.
```

## Running FLaP
FLaP can merge the LaTeX source into a single LaTeX file, and adjust the graphics inclusion directives.
To do so, we invoke FLaP as follows:

	$> python3 -m flap project/main.tex output

> Note that prior to version 0.2.3, the main module was flap.ui. To run FLaP with earlier versions, one has input 
`python3 -m flap.ui main.tex output`.

> You may as well use the "verbose" option (`-v`) to get more details about what FLaP is doing.

This will create a directory `output`, with the following contents:

	output/
		merged.tex
		screenshot.pdf
		
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