# Known Caveats

There is at least one situation that FLaP will *NOT* handle:

 * The use of inclusion directives in user-defined commands (e.g., using `\newcommand`).

> Until version 0.4.1, FLaP was simply matching regular expressions, and was not
able to handle verbatim environment properly.

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