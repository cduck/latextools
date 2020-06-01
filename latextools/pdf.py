import base64


class Pdf:
    def __init__(self, fname=None, data=None, width='100%',
                 height='300px', border=False, log=None):
        self.fname = fname
        self.data = data
        self.width = width
        self.height = height
        self.border = border
        self.log = log

    def save(self, fname):
        with open(fname, 'wb') as f:
            f.write(self.data)

    def rasterize(self, to_file=None, scale=1):
        return self.as_svg().rasterize(to_file=to_file, scale=scale)

    def as_svg(self):
        from .convert import pdf_to_svg
        return pdf_to_svg(self)

    def toDrawables(self, elements, **kwargs):
        '''Integration with drawSvg.

        Forwards its arguments to `latextools.convert.Svg.toDrawables`.
        '''
        svg = self.as_svg()
        return svg.toDrawables(elements, **kwargs)

    def _repr_html_(self):
        if self.data is None and self.fname is None:
            return '<span color="red">No PDF.</span>'
        if self.data is None:
            path = self.fname
        else:
            path = (b'data:application/pdf;base64,'
                     + base64.b64encode(self.data)
                    ).decode()
        return (
f'''<iframe src="{path}"{' style="border:0"'*(not self.border)}
        width="{self.width}" height="{self.height}">
    No iframe support.
</iframe>''')
