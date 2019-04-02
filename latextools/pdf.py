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
