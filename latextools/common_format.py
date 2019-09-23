from . import str_util
from . import LatexContentAbc

class WrapContent(LatexContentAbc):
    def __init__(self, pre_code, post_code, content):
        super().__init__((), (), None)
        self.pre_code = pre_code
        self.post_code = post_code
        self.content = content

    def list_sub_content(self):
        return [self.content]

    def _latex_code_body(self, indent=''):
        pre = str_util.prefix_lines(indent, self.pre_code)
        post = str_util.prefix_lines(indent, self.post_code)
        body = self.content.latex_code_body(indent=indent)
        return '\n'.join([pre, body, post])

def centering_content(content):
    return WrapContent('\centering', '', content)
