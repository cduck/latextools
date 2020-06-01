
from .project import LatexProject
from .content import BasicContent
from .document import DocumentConfig, STANDALONE_CONFIG
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
        config = DocumentConfig('standalone')
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
    q_conf = '@R={} @C{}'.format(r, c)
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
