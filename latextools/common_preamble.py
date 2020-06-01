from .package import LatexPackage
from .command import (
    LatexCommand,
    CommandBundle,
)
from .content import (
    LatexContentAbc,
    BasicContent,
    MultiContent,
)
from .document import (
    DocumentConfig,
)


class pkg:
    def __getattr__(self, key):
        return LatexPackage(key)
pkg = pkg()

def geometry_config(margin='1.0in'):
    return LatexPackage('geometry', [f'margin={margin}'])
pkg.geometry = geometry_config()
pkg.inputenc = LatexPackage('inputenc', ['utf8'])

pkg.xcolor = LatexPackage('xcolor')
pkg.pagecolor = LatexPackage('pagecolor')
pkg.multicol = LatexPackage('multicol')
pkg.fancyhdr = LatexPackage('fancyhdr')

pkg.amsmath = LatexPackage('amsmath')
pkg.commath = LatexPackage('commath')
pkg.amsfonts = LatexPackage('amsfonts')
pkg.amssymb = LatexPackage('amssymb')
pkg.mathtools = LatexPackage('mathtools')

def tikz_config(use=()):
    return LatexPackage('tikz', setup_content=
            '\n'.join(fr'\usetikzlibrary{{{u}}}' for u in use))
pkg.tikz = tikz_config(use=['patterns', 'arrows', 'external'])

def pgfplots_config(compat=1.14):
    return LatexPackage('pgfplots', packages=[pkg.tikz], setup_content=
            fr'\pgfplotsset{{compat={compat}}}')
pkg.pgfplots = pgfplots_config()

pkg.siunitx = LatexPackage('siunitx', options=['detect-family'])
pkg.sansmath = LatexPackage('sansmath', options=['eulergreek'])
pkg.relsize = LatexPackage('relsize')

pkg.cite = LatexPackage('cite')

pkg.qcircuit = LatexPackage('qcircuit', options=['braket'])
pkg.svg = LatexPackage('svg')


class cmd: pass
cmd = cmd()

cmd.all_math = CommandBundle(packages=[
            pkg.amsmath,
            pkg.commath,
            pkg.amsfonts,
            pkg.amssymb,
            pkg.mathtools,
        ])

cmd.sisetup = LatexCommand('sisetup', r'\sisetup{text-sf=\sansmath}',
            packages=[pkg.siunitx, pkg.sansmath])
cmd.artist_deps = CommandBundle(
        cmd.sisetup,
        packages=[
            pkg.tikz,
            pkg.pgfplots,
            pkg.siunitx,
            pkg.sansmath,
            pkg.relsize,
        ])

cmd.TODO = LatexCommand('TODO',
            r'\newcommand{\TODO}[1][TODO]{{\colorbox{red}{\textbf{\textcolor{white}{#1}}}}}',
            packages=[pkg.xcolor])

cmd.ceil = LatexCommand('ceil',
            r'\DeclarePairedDelimiter{\ceil}{\lceil}{\rceil}',
            packages=[pkg.mathtools])


class Title(LatexContentAbc):
    def __init__(self, title=None, author=None, date=None):
        super().__init__((), (), 'Make title')
        self.title = title
        self.author = author
        self.date = date

    def _latex_code_body(self, indent=''):
        lines = []
        if self.title:
            lines.append(fr'\title{{{self.title}}}')
        if self.author:
            lines.append(fr'\author{{{self.author}}}')
        if self.date:
            lines.append(fr'\date{{{self.date}}}')
        lines.append(f'\maketitle')
        return '\n'.join(f'{indent}{l}' for l in lines)


class Color(LatexCommand):
    def __init__(self, color_name, r, g, b):
        code = fr'\definecolor{{{color_name}}}{{{r},{g},{b}}}'
        super().__init__('color_'+color_name, code, packages=[pkg.xcolor])
        self.color_name = color_name
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return self.color_name

def set_page_color(bg=None, fg=None):
    assert (bg is not None) + (fg is not None) >= 1
    commands = []
    if isinstance(bg, Color):
        commands.append(bg)
    if isinstance(fg, Color):
        commands.append(fg)
    lines = []
    if bg is not None:
        lines.append(fr'\pagecolor{{{str(bg)}}}')
    if fg is not None:
        lines.append(fr'\color{{{str(fg)}}}')
    code = '\n'.join(lines)
    return LatexCommand('pagecolor', code, packages=[pkg.pagecolor])


basic_config = DocumentConfig('article', ['11pt', 'letterpaper'],
            packages=[pkg.geometry, pkg.inputenc])
