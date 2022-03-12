import os
import subprocess
import fs.tempfs

from .project import LatexProject
from .content import BasicContent
from .document import DocumentConfig, STANDALONE_CONFIG
from .command import LatexCommand
from .file import PlainTextFile, BinaryFile
from .common_preamble import pkg


def render_snippet(content=r'$Z\cdot Y=X$', *packages, commands=(),
                   lpad=0, rpad=0, tpad=0, bpad=0, pad=None,
                   config=STANDALONE_CONFIG):
    '''Easy way to render a small snippet of Latex code.

    Use `latextools.pkg` and `.cmd` for quick package and command definitions.

    Returns a Pdf object.  Save with `obj.save('file.pdf')`.  Add to drawing
    with `d.draw(obj)` (using drawSvg).
    '''
    if pad is not None:
        lpad, bpad, rpad, tpad = (pad,) * 4
    if config is None:
        config = STANDALONE_CONFIG
    if (lpad, bpad, rpad, tpad) != (0, 0, 0, 0):
        padding = [p if isinstance(p, str) else '{}pt'.format(p)
                   for p in (lpad, bpad, rpad, tpad)]
        border_conf = 'border={{{}}}'.format(' '.join(padding))
        if (config.doc_type == 'standalone'
                and not any(option.startswith('border=')
                            for option in config.options)):
            config = DocumentConfig(
                'standalone', options=(*config.options, border_conf),
                packages=config.packages, commands=config.commands)
    proj = LatexProject()
    content = BasicContent(content, packages, commands)
    proj.add_file(content.as_document(path='main.tex', config=config))
    r = proj.compile_pdf(options=['-halt-on-error', '-file-line-error',
                                  '-interaction', 'nonstopmode',
                                  '-shell-escape'])
    return r

def render_qcircuit(content=r'& \gate{X} & \qw', *packages, r=0.5, c=0.7,
                    const_size=False, const_row=False, const_col=False,
                    lpad=1, rpad=1, tpad=1, bpad=1, pad=None,
                    commands=(), config=None):
    '''Easy way to render a qcircuit diagram.

    Use `latextools.pkg` and `.cmd` for quick package and command definitions.

    Returns a Pdf object.  Save with `obj.save('file.pdf')`.  Add to drawing
    with `d.draw(obj)` (using drawSvg).
    '''
    if not isinstance(r, str):
        r = '{}em'.format(r)
    if not isinstance(c, str):
        c = '{}em'.format(c)
    q_conf = '@R={} @C={}'.format(r, c)
    if const_row:
        q_conf += ' @!R'
    if const_col:
        q_conf += ' @!C'
    if const_size:
        q_conf += ' @!'
    content = '\\Qcircuit {} {{\n{}\n}}'.format(q_conf, content.strip())
    return render_snippet(content,
        pkg.qcircuit, *packages, lpad=lpad, rpad=rpad, tpad=tpad, bpad=bpad,
        pad=pad, commands=commands, config=config)

_SAMPLE_SVG = r'''<svg width="50" height="50" viewBox="0 -50 50 50">
<circle cx="25" cy="-25" r="25" />
<text x="25" y="-20" font-size="25" fill="lime" text-anchor="middle">\large$\sqrt{5}$</text>
</svg>'''
def render_svg(text_fname_or_drawing=_SAMPLE_SVG, *packages, commands=(),
               config=STANDALONE_CONFIG, width=None, inkscape='inkscape',
               inkscape_args=('-z', '-C', '--export-latex')):
    r'''Easy way to render an SVG with the LaTeX svg package.

    All text in the SVG will be rendered by LaTeX, including math and macros.
    Use `latextools.pkg` and `.cmd` for quick package and command definitions.

    Returns a Pdf object.  Save with `obj.save('file.pdf')`.  Add to drawing
    with `d.draw(obj)` (using drawSvg).

    This function renders equivalent to the following in a LaTeX project:

        \usepackage{svg}
        \svgsetup{inkscapeopt=-C}  % Use SVG page bounds instead of content
        % ...
        \includesvg{image.svg}
        % Or \includesvg[width=\columnwidth]{image.svg}
    '''
    text, fname = None, None
    if hasattr(text_fname_or_drawing, 'asSvg'):
        text = text_fname_or_drawing.asSvg()
    elif hasattr(text_fname_or_drawing, 'as_svg'):
        text = text_fname_or_drawing.as_svg()
    elif os.path.exists(text_fname_or_drawing):
        fname = text_fname_or_drawing
    else:  # Assume valid SVG content
        text = text_fname_or_drawing

    packages = (pkg.svg,) + packages  # SVG package is required
    #commands = ((LatexCommand('svgsetup', r'\svgsetup{inkscapeopt=-C}'),)
    #            + commands)
    if config is None:
        config = STANDALONE_CONFIG
    inc = (r'\includesvg{image.svg}' if width is None
           else rf'\includesvg[width={width}]{{image.svg}}')

    with fs.tempfs.TempFS() as tmp_dir:  # Directory to run Inkscape
        proj = LatexProject(tmp_dir)
        proj.add_file(PlainTextFile('image.svg', text=text, fname=fname))
        # Compile SVG
        svg_path = tmp_dir.getsyspath('/image.svg')
        render_path = tmp_dir.getsyspath('/image_svg-tex.pdf')
        render_svg_intermediate(
                svg_path, inkscape=inkscape, inkscape_args=inkscape_args)
        proj.add_file(BinaryFile('image_svg-tex.pdf', fname=render_path))
        if tmp_dir.exists('/image_svg-tex.pdf_tex'):
            proj.add_file(PlainTextFile(
                    'image_svg-tex.pdf_tex', fname=f'{render_path}_tex'))
        # Compile PDF
        content = BasicContent(inc, packages, commands)
        proj.add_file(content.as_document(path='main.tex', config=config))
        r = proj.compile_pdf(options=[
                '-halt-on-error', '-file-line-error', '-interaction',
                'nonstopmode', '-shell-escape'])
    return r

def render_svg_intermediate(text_fname_or_drawing=_SAMPLE_SVG,
                            svg_fname=None,
                            inkscape='inkscape',
                            inkscape_args=('-z', '-C', '--export-latex')):
    text, fname = None, None
    if hasattr(text_fname_or_drawing, 'asSvg'):
        text = text_fname_or_drawing.asSvg()
    elif hasattr(text_fname_or_drawing, 'as_svg'):
        text = text_fname_or_drawing.as_svg()
    elif os.path.exists(text_fname_or_drawing):
        fname = text_fname_or_drawing
    else:  # Assume valid SVG content
        text = text_fname_or_drawing
    if svg_fname is None:
        svg_fname = 'image.svg' if fname is None else fname
    out_dir, out_base = os.path.split(svg_fname)
    if fname is None:
        with open(svg_fname, 'w') as f:
            f.write(text)
    else:
        svg_fname = fname
    render_path = os.path.join(out_dir, f'{out_base.replace(".", "_")}-tex.pdf')
    ret = subprocess.call([
            inkscape, *inkscape_args, f'--export-file={render_path}',
            svg_fname])
    if ret != 0:
        raise RuntimeError('Inkscape failed to convert svg to PDF+LaTeX')
    if '--export-latex' in inkscape_args:
        return render_path, f'{render_path}_tex'
    else:
        return render_path,
