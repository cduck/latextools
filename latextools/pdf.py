import base64


class Pdf:
    def __init__(self, fname=None, data=None, width='100%',
                 height='300px', border=False):
        if (fname is not None) + (data is not None) < 1:
            raise TypeError('Specify either the fname or data argument.')
        self.fname = fname
        self.data = data
        self.width = width
        self.height = height
        self.border = border

    def _repr_html_(self):
        if self.data is None:
            path = self.fname
        else:
            path = (b'data:application/pdf;base64,'
                     + base64.b64encode(self.data)
                    ).decode()
        return (
f'''<iframe src="{path}"{' frameBorder="0"'*(not self.border)}
        width="{self.width}" height="{self.height}">
    No iframe support.
</iframe>''')
