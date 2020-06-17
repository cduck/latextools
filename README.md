![LatexTools logo](https://raw.githubusercontent.com/cduck/latextools/master/examples/logo.svg)

# LatexTools

latextools is a collection of tools for building, rendering, and converting Latex documents.
Output objects integrate with Jupyter and display inline after a code cell allowing for quick design of many Latex diagrams like Tikz and qcircuit.


# Install

latextools is available on PyPI:

```bash
python3 -m pip install latextools
```

## Prerequisites

### pdflatex

A distribution of LaTeX that provides the `pdflatex` command needs to be installed separately.
There are many options and instillation is platform-specific.
Below are some examples for installing TeX Live on Linux and MacTeX on macOS.

**Ubuntu**

```bash
sudo apt install texlive  # Or texlive-latex-recommended, or texlive-latex-extra
```

**macOS**

Using [homebrew](https://brew.sh/):

```bash
brew cask install mactex  # Or mactex-no-gui
```

### Inkscape (optional)

[Inkscape](https://inkscape.org/) is used for conversions from PDF to other image formats.

**Any OS**

Download and run the installer from [inkscape.org](https://inkscape.org/release/).

**macOS**

Using [homebrew](https://brew.sh/):

```bash
brew cask install inkscape
```

### drawSvg and Cairo (optional)

[drawSvg](https://github.com/cduck/drawSvg/) and [Cairo](https://www.cairographics.org/download/) are used for some SVG conversion functions.

**Ubuntu**

```bash
sudo apt-get install libcairo2
python3 -m pip install drawSvg
```

**macOS**

Using [homebrew](https://brew.sh/):

```bash
brew install cairo
python3 -m pip install drawSvg
```


# Examples

### Easily render a bit of Latex code
```python
import latextools
import random

numbers = [[random.randint(0, 10000) for x in range(4)]
          for y in range(5)]
row = ['&'.join('{}'.format(num) for num in row)
       for row in numbers]
table_body = ' \\\\\n\\hline\n    '.join(row)

pdf = latextools.render_snippet(r'''
\begin{tabular}{c|c|c|c}
    A & B & C & E \\
    \hline\hline
    ''' + table_body + ''' \\
\end{tabular}
'''.strip(),
    pad=1,
)
pdf.save('table.pdf')
pdf.rasterize('table.png', scale=2)
pdf.as_svg().as_drawing(scale=2).saveSvg('table.svg')
pdf  # Show preview if this is in a Jupyter notebook
```
![Example table output](https://raw.githubusercontent.com/cduck/latextools/master/examples/table.png)

### Draw a qcircuit diagram

```python
import latextools

pdf = latextools.render_qcircuit(r'''
% qcircuit code from http://physics.unm.edu/CQuIC/Qcircuit/Qtutorial.pdf
& \ctrl{2} & \qw & \gate{H} & \ctrl{1} &\gate{H} & \qw \\
& \qw & \ctrl{1} & \gate{H} & \targ &\gate{H} & \qw \\
& \targ & \targ & \gate{Z} & \qw & \ctrl{-1} &\qw \gategroup{1}{4}{2}{6}{.7em}{--}
''')
pdf.save('qcircuit.pdf')
pdf.rasterize('qcircuit.png', scale=2)
pdf.as_svg().as_drawing(scale=2).saveSvg('qcircuit.svg')
pdf  # Show preview if this is in a Jupyter notebook
```

![Example qcircuit output](https://raw.githubusercontent.com/cduck/latextools/master/examples/qcircuit.png)

### Embed latex in an SVG vector drawing

```python
import latextools
import drawSvg as draw  # pip3 install drawSvg

# Render latex
latex_eq = latextools.render_snippet(
    r'$\sqrt{X^\dag}$',
    commands=[latextools.cmd.all_math])
svg_eq = latex_eq.as_svg()

# Use the rendered latex in a vector drawing
d = draw.Drawing(100, 100, origin='center', displayInline=False)
d.append(draw.Circle(0, 0, 49, fill='yellow', stroke='black', stroke_width=2))
d.draw(svg_eq, x=0, y=0, center=True, scale=2.5)

d.saveSvg('vector.svg')
d.savePng('vector.png')

# Display in Jupyter notebook
#d.rasterize()  # Display as PNG
d  # Display as SVG
```

![Example qcircuit output](https://raw.githubusercontent.com/cduck/latextools/master/examples/vector.png)

### Build and render a full Latex project

```python
import latextools

# Build a Latex document
packages = [
    latextools.pkg.qcircuit,
    latextools.LatexPackage('geometry', ('paperheight=2.5in','paperwidth=2.5in',
                                         'margin=0.1in','heightrounded')),
]
commands = [
    latextools.cmd.ceil,
]
config = latextools.DocumentConfig('article', ('',))

proj = latextools.LatexProject()
content = latextools.BasicContent(
    r'''%
\[
\Qcircuit @R=.1em @C=0.3em @!R {
&	\qw	&	\qw	&	\ctrl{2}	&	\qw	&	\qw	&	\qw	&	\qw	&	\qw	&	\qw	\\
&	\qw	&	\qw	&	\qw	&	\qw	&	\ctrl{1}	&	\qw	&	\qw	&	\qw	&	\qw	\\
&	\push{\ket{0}}\qw	&	\qw	&	\targ	&	\targ	&	\targ	&	\targ	&	\qw	&	\meter	&	\qw	\\
&	\qw	&	\qw	&	\targ	&	\ctrl{-1}	&	\qw	&	\qw	&	\qw	&	\qw	&	\qw	\\
&	\qw	&	\qw	&	\qw	&	\targ	&	\qw	&	\ctrl{-2}	&	\qw	&	\qw	&	\qw	\\
&	\push{\ket{0}}\qw	&	\gate{H}	&	\ctrl{-2}	&	\ctrl{-1}	&	\ctrl{1}	&	\ctrl{2}	&	\gate{H}	&	\meter	&	\qw	\\
&	\qw	&	\qw	&	\qw	&	\qw	&	\targ	&	\qw	&	\qw	&	\qw	&	\qw	\\
&	\qw	&	\qw	&	\qw	&	\qw	&	\qw	&	\targ	&	\qw	&	\qw	&	\qw	\\
}%
\]
''',
    packages, commands)
doc = content.as_document(path='figs/syndrome-circuit.tex',
                          config=config)
doc = latextools.LatexDocument(
    path='figs/syndrome-circuit.tex', config=config,
    contents=(
        latextools.BasicContent('\centering A qcircuit diagram:'),
        content,
    ))
proj.add_file(doc)

# Write Latex source code to current directory (maintains directory structure)
proj.write_src('.')

# Render Latex
proj.add_file(latextools.LatexDocument(
    path='main.tex', config=config, contents=doc.contents))
pdf = proj.compile_pdf()
# With additional command line arguments:
#pdf = proj.compile_pdf(options=['-halt-on-error', '-file-line-error',
#                                '-interaction', 'nonstopmode', '-shell-escape'])

pdf.save('figs/syndrome-circuit.pdf')
pdf  # Show preview if this is in a Jupyter notebook
```

![Example Latex output](https://raw.githubusercontent.com/cduck/latextools/master/examples/syndrome-circuit.png)
