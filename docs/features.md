# Detected LaTeX Commands

Here is the list of LaTeX commands or environments that FLaP detects and adjusts.

 * File inclusions directives:
    * `\input`;
    * `\include`;
    * `\includeonly`;
    * `\subfile` from package [`subfiles`](https://www.ctan.org/pkg/subfiles?lang=en).
 * Graphics inclusion directives:
    * `\includegraphics`;
    * `\graphicspath`;
    * Experimental! `\includesvg` from package [`svg`](https://www.ctan.org/pkg/svg?lang=en).
 * Beamer directives:
    * `\begin{overpic}`;
    * `\endinput`.
    
Note the [FLaP limitations](caveats): FLaP will not process properly any of these commands if:

 * they are used in a `verbatim`e environment;
 * they are used within a used-defined command.