import abc


INDENT_STEP = ' '*4


class LatexContentAbc(metaclass=abc.ABCMeta):
    def __init__(self, packages, commands, comment=None):
        self.packages = packages
        self.commands = commands
        self.comment = comment

    def list_sub_content(self):
        '''Optionally override in subclass.'''
        return ()

    def required_packages(self):
        yield from self.packages
        for c in self.commands:
            yield from c.required_packages()
        for sub in self.list_sub_content():
            yield from sub.required_packages()

    def required_commands(self):
        yield from self.commands
        for p in self.packages:
            yield from p.required_commands()
        for sub in self.list_sub_content():
            yield from sub.required_commands()

    def latex_code_body(self, indent=''):
        out = ''
        if self.comment:
            out += '\n'.join(f'{indent}% {line}'
                             for line in self.comment.split('\n'))
            out += '\n'
        out += self._latex_code_body(indent=indent)
        return out

    @abc.abstractmethod
    def _latex_code_body(self, indent=''):
        pass


class BasicContent(LatexContentAbc):
    def __init__(self, latex_code, packages=(), commands=(), comment=None):
        super().__init__(packages, commands, comment=comment)
        self.latex_code = latex_code

    def _latex_code_body(self, indent=''):
        return '\n'.join(f'{indent}{s}'.rstrip()
                         for s in self.latex_code.strip().split('\n'))


class MultiContent(LatexContentAbc):
    def __init__(self, *contents, comment=None):
        super().__init__((), (), comment=comment)
        self.contents = list(contents)

    def list_sub_content(self):
        return self.contents

    def _latex_code_body(self, indent=''):
        return '\n\n'.join(filter(bool, (c.latex_code_body(indent=indent)
                                         for c in self.contents)))
