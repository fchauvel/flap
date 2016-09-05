# Known Caveats

There are at least two situations that FLaP will *NOT* handle:

 * the use of a `verbatim` environmnent contains file inclusion 
 directives such as `\input`, `\include`, etc.;
 
 * The use of inclusion directives in user-defined commands (e.g., using `\newcommand`).


FLaP is a simple Python script that naively substitutes predefined patterns
in your LaTeX sources. When FLaP matches a pattern, it has not prior knowledge of what has been subsituted before. 
For FLaP to handle the two cases would requires parsing and interpreting the LaTeX source.

## LaTeX code in `verbatim` Environments

The first caveats is illustrated in the following example:

````latex
\begin{verbatim}
    % Here is some sample LaTeX code
    \input{src/my-file}
\end{verbatim}
````

FLaP will actually matches the `input{src/my-file}` and try to access the associated file, which is unlikely to exist.


## Inclusions Directives Wrapped into User-defined Commands 

FLaP is not able to detect that an inclusion directive is actually 
wrapped into a used-defined command as I do below:

````latex
\newcommand{\myinput}[1]{%
    \input{#1}%
}
````

Here, FLaP will also try to open the file named `#1.tex`, which is very 
unlikely to exist. 