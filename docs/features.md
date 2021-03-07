# Detected LaTeX Commands

Here is the list of LaTeX commands or environments that FLaP detects
and/or adjusts.

 * File inclusions directives:
    * `\input`;
    * `\include`;
    * `\includeonly`;
    * `\subfile` from package
      [`subfiles`](https://www.ctan.org/pkg/subfiles?lang=en) (since
      v0.4.0).
 * Graphics inclusion directives:
    * `\includegraphics`;
    * `\graphicspath`(since  v0.3.0);
    * Experimental! `\includesvg` from package
      [`svg`](https://www.ctan.org/pkg/svg?lang=en).
 * Environments:
    * `\begin{verbatim}...\end{verbatim}`(since v0.5.0)
 * Beamer directives:
    * `\begin{overpic};
    * `\endinput`.
 * Bibliography Management
    * `\bibliography`
    * Biblatex `\addbibresource` (since 0.6.0)
    
Note the [FLaP limitations](caveats): FLaP will not process properly
any of these commands if they are used within a used-defined command.

> Versions prior to 0.5 cannot identify LaTeX commands within a
`verbatim` environment and may perform invalid substitutions.
