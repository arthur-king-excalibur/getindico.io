\batchmode

<%block name="document_class">
\documentclass[a4paper, 15pt]{article} %% document type
</%block>

<%block name="geometry">
\usepackage[a4paper, top=1em, bottom=10em]{geometry}
</%block>

\usepackage{cmbright}
\usepackage[T1]{fontenc}
\usepackage[utf8x]{inputenc}
\usepackage{lmodern}
\usepackage{hyperref}


\usepackage[english]{babel}
\usepackage[final, babel]{microtype} %% texblog.net/latex-archive/layout/pdflatex-microtype/

\usepackage{float} %% improved interface for floating objects
\usepackage[export]{adjustbox}
\usepackage[usenames,dvipsnames]{xcolor} %% named colors
\usepackage{sectsty} %% style sections
\usepackage{xstring}
\usepackage[inline]{enumitem}

<%block name="header_extra">
</%block>


\begin{document}

    %% set fonts
    \renewcommand{\sfdefault}{cmbr}
    \renewcommand*{\familydefault}{\sfdefault}

    %% no indentation
    \setlength{\parindent}{0cm}

    %% helper commands

    \newcommand{\truncateellipses}[2]{
       \StrLeft{#1}{#2}[\truncated]
       \truncated
       \IfStrEq{\truncated}{#1}{}{\dots}
    }

    %% remove section heading numbering
    \setcounter{secnumdepth}{0}

    <%block name="content">
    </%block>

\end{document}
