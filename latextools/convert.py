import base64
from pathlib import Path
import subprocess
import tempfile
import re
import urllib

import fs

from .project import LatexProject, LatexError
from .package import LatexPackage
from .content import BasicContent
from .document import DocumentConfig
from .command import LatexCommand


svg_packages = (
    LatexPackage('xcolor'),
    LatexPackage('amsmath'),
    LatexPackage('amssymb'),
    LatexPackage('amsfonts'),
    LatexPackage('svg'),
    LatexPackage('qcircuit', options=['braket', 'qm']),
)
svg_commands = (
)


def svg_to_pdf(fname_or_drawing=None, text=None, data=None, file=None,
               fit_drawing=False, latex_width=None, out_name=None,
               only_final=True, config=DocumentConfig('standalone'),
               **pdf_args):
    '''Requires the inkscape command line tool.'''
    if ((fname_or_drawing is not None)
            + (text is not None)
            + (data is not None)
            + (file is not None)) != 1:
        raise TypeError(
                'Specify exactly one of fname_or_drawing, text, data, file, or '
                'fname.')

    fname = None
    if fname_or_drawing:
        if isinstance(fname_or_drawing, (str, bytes, Path)):
            fname = fname_or_drawing
        else:
            text = fname_or_drawing.asSvg()

    proj = LatexProject()
    proj.add_file('image.svg', text=text, data=data, file=file, fname=fname)

    if latex_width is None:
        width_str = ''
    else:
        width_str = r'\def\svgwidth'+f'{{{latex_width}}}\n'
    content = BasicContent(width_str+r'\input{image_svg-tex.pdf_tex}',
                           svg_packages, svg_commands)
    doc = content.as_document('main.tex', config=config)
    proj.add_file(doc)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_fs = fs.open_fs(tmp_dir, writeable=False)
        fs.copy.copy_file(proj.proj_fs, 'image.svg', tmp_fs, 'image.svg')
        if fit_drawing:
            options = ('-z', '-D', '--export-latex', '--export-type=pdf')
        else:
            options = ('-z', '--export-latex', '--export-type=pdf')
        _run_inkscape(proj, 'image.svg', tmp_dir, options=options)
        tmp_fs.remove('image.svg')
        proj.proj_fs.remove('image.svg')

        r = proj.compile_pdf(options=['-shell-escape', '-halt-on-error',
                                      '-file-line-error', '-interaction',
                                      'nonstopmode'],
                             tmp_dir=tmp_dir,
                             #inkscape_list=['image.svg'],
                             **pdf_args)

        if out_name is not None:
            if out_name.endswith('.svg') or out_name.endswith('.pdf'):
                out_name = out_name[:-4]

            r.save(out_name + '.pdf')

            def save_intermediate(fname, ext):
                out_fname = out_name + ext
                data = None
                if tmp_fs.exists(fname):
                    fs.copy.copy_file(tmp_fs, fname, '.', out_fname)
            if not only_final:
                save_intermediate('image_svg-tex.pdf_tex', '_svg-tex.pdf_tex')
                save_intermediate('image_svg-tex.pdf', '_svg-tex.pdf')
    return r

def _run_inkscape(proj, fpath, cwd,
                 options=('-z', '--export-latex', '--export-type=pdf')):
    try:
        out_path = fpath
        if not out_path.endswith('.svg'):
            out_path += '.svg'
        out_path = out_path[:-4] + '_svg-tex.pdf'
        args = ['inkscape', *options, fpath, '-o', out_path]
        p = subprocess.Popen(args,
                             cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise LatexError('inkscape command not found.')
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        # inkscape had an error
        msg = ''
        if stdout:
            msg += stdout.decode()
        if stderr:
            msg += stderr.decode()
        raise LatexError(msg)


class Svg:
    STRIP_CHARS = ('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10'
                   '\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e'
                   '\x1f')

    def __init__(self, content):
        self.content = content
        w_str = next(re.finditer(r'width="([0-9]+(.[0-9]+)?)', self.content)
                    ).group(1)
        h_str = next(re.finditer(r'height="([0-9]+(.[0-9]+)?)', self.content)
                    ).group(1)
        self.width, self.height = float(w_str)*4/3, float(h_str)*4/3

    def _repr_svg_(self):
        return self.content

    def save(self, fname):
        with open(fname, 'w') as f:
            f.write(self.content)

    def rasterize(self, to_file=None, scale=1):
        '''Requires the drawSvg Python package and cairo.'''
        import drawSvg as draw
        if scale != 1:
            return self.as_drawing(scale=scale).rasterize(to_file)
        else:
            if to_file:
                return draw.Raster.fromSvgToFile(self.content, to_file)
            else:
                return draw.Raster.fromSvg(self.content)

    def as_drawing(self, scale=1):
        '''Requires the drawSvg Python package and cairo.'''
        import drawSvg as draw
        d = draw.Drawing(self.width*scale, self.height*scale)
        d.draw(self, x=0, y=0, scale=scale)
        return d

    def asDataUri(self, strip_chars=STRIP_CHARS):
        '''Returns a data URI with base64 encoding.'''
        data = self.content
        search = re.compile('|'.join(strip_chars))
        data_safe = search.sub(lambda m: '', data)
        b64 = base64.b64encode(data_safe.encode())
        return 'data:image/svg+xml;base64,' + b64.decode(encoding='ascii')

    def asUtf8DataUri(self, unsafe_chars='"', strip_chars=STRIP_CHARS):
        '''Returns a data URI without base64 encoding.

        The characters '#&%' are always escaped.  '#' and '&' break parsing of
        the data URI.  If '%' is not escaped, plain text like '%50' will be
        incorrectly decoded to 'P'.  The characters in `strip_chars` cause the
        SVG not to render even if they are escaped.
        '''
        data = self.content
        unsafe_chars = (unsafe_chars or '') + '#&%'
        replacements = {
            char: urllib.parse.quote(char, safe='')
            for char in unsafe_chars
        }
        replacements.update({
            char: ''
            for char in strip_chars
        })
        search = re.compile('|'.join(map(re.escape, replacements.keys())))
        data_safe = search.sub(lambda m: replacements[m.group(0)], data)
        return 'data:image/svg+xml;utf8,' + data_safe

    def toDrawables(self, elements, x=0, y=0, center=False, scale=1,
                    text_anchor=None, **kwargs):
        scale = scale*4/3  # Points to pixels
        w_str = next(re.finditer(r'width="([0-9]+(.[0-9]+)?)', self.content)
                    ).group(1)
        h_str = next(re.finditer(r'height="([0-9]+(.[0-9]+)?)', self.content)
                    ).group(1)
        w, h = float(w_str), float(h_str)
        x_off, y_off = 0, 0
        if center:
            x_off, y_off = -w/2, h/2
        else:
            x_off, y_off = 0, h
        if text_anchor == 'start':
            x_off = 0
        elif text_anchor == 'middle':
            x_off = -w/2
        elif text_anchor == 'end':
            x_off = -w

        id_prefix = f'embed-{hash(self.content)}-'
        content = (self.content
                    .replace('id="', f'id="{id_prefix}')
                    .replace('="url(#', f'="url(#{id_prefix}')
                    .replace('xlink:href="#', f'xlink:href="#{id_prefix}'))
        defs_str = next(re.finditer(r'<defs>(.*)</defs>', content,
                                    re.MULTILINE | re.DOTALL)
                       ).group(1)
        elems_str = next(re.finditer(r'</defs>(.*)</svg>', content,
                                     re.MULTILINE | re.DOTALL)
                        ).group(1)
        defs = elements.Raw(defs_str)

        transforms = []
        if 'transform' in kwargs:
            transforms.append(kwargs['transform'])
        if x or y:
            transforms.append(f'translate({x}, {-y})')
        transforms.append(f'scale({scale})')
        if x_off or y_off:
            transforms.append(f'translate({x_off}, {-y_off})')
        kwargs['transform'] = ' '.join(transforms)

        elems = elements.Raw(elems_str, (defs,), **kwargs)
        return (elems,)


def pdf_to_svg(fname_or_obj=None, text=None, data=None, file=None,
               out_name=None, ret_svg=True):
    '''Requires the pdf2svg command line tool.'''
    if ((fname_or_obj is not None)
            + (text is not None)
            + (data is not None)
            + (file is not None)) != 1:
        raise TypeError(
                'Specify exactly one of fname_or_obj, text, data, file, or '
                'fname.')

    fname = None
    if fname_or_obj is not None:
        if isinstance(fname_or_obj, (str, bytes, Path)):
            fname = fname_or_obj
        elif fname_or_obj.fname is not None:
            fname = fname_or_obj.fname
        else:
            data = fname_or_obj.data
    if fname is not None:
        with open(fname, 'b') as f:
            pdf_to_svg(file=f, out_name=out_name)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_fs = fs.open_fs(tmp_dir, writeable=True)
        if file is not None:
            tmp_fs.writefile('image.pdf', file)
        elif data is not None:
            tmp_fs.writebytes('image.pdf', data)
        elif text is not None:
            tmp_fs.writetext('image.pdf', text)
        else:
            assert False, 'Logic error'

        args = ['pdf2svg', 'image.pdf', 'image.svg']
        try:
            p = subprocess.Popen(args,
                                 cwd=tmp_dir,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise LatexError('inkscape command not found.')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            # pdf2svg had an error
            msg = ''
            if stdout:
                msg += stdout.decode()
            if stderr:
                msg += stderr.decode()
            raise RuntimeError(msg)

        if out_name is not None:
            fs.copy.copy_file(tmp_fs, 'image.svg', '.', out_name)

        if ret_svg:
            return Svg(tmp_fs.readtext('image.svg'))


def render_latex_in_svg(name_or_drawing=None, text=None, data=None, file=None,
                        fit_drawing=False, latex_width=None, out_name=None,
                        config=DocumentConfig('standalone'), ret_svg=True):
    pdf = svg_to_pdf(name_or_drawing, text=text, data=data, file=file,
                     fit_drawing=fit_drawing, latex_width=latex_width,
                     out_name=None, config=config)
    svg = pdf_to_svg(pdf, out_name=out_name, ret_svg=ret_svg)
    return svg

def svg_to_png(name_or_drawing=None, text=None, data=None, file=None,
               fit_drawing=False, latex_width=None, out_name=None,
               config=DocumentConfig('standalone')):
    svg = render_latex_in_svg(name_or_drawing, text=text, data=data, file=file,
                              fit_drawing=fit_drawing, latex_width=latex_width,
                              config=config)
    png = svg.rasterize(out_name)
    return png

def text_to_svg(latex_text, config=DocumentConfig('standalone'), fill=None):
    color = fill
    commands = list(svg_commands)
    color_command = None
    if color is not None:
        if color.startswith('#') and (len(color) == 7 or len(color) == 4):
            w = (len(color)-1) // 3
            r = int(color[1:1+w]*(3-w), 16)
            g = int(color[1+w:1+2*w]*(3-w), 16)
            b = int(color[1+2*w:1+3*w]*(3-w), 16)
            color_command = (r'\definecolor{customcolor}{RGB}'
                             f'{{{r},{g},{b}}}')
            color = 'customcolor'
    if color_command is not None:
        commands.append(LatexCommand('customcolor', color_command))
    if color is not None:
        latex_text = fr'\color{{{color}}}{latex_text}'

    content = BasicContent(latex_text, svg_packages, commands)
    pdf = content.render(config=config)
    return pdf_to_svg(pdf)
