import abc

import fs

from . import str_util, document, project


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

    def get_required_files(self):
        for content in self.list_sub_content():
            yield from content.get_required_files()

    def latex_code_body(self, indent=''):
        out = ''
        if self.comment:
            out += str_util.prefix_lines(indent+'% ', self.comment)
            out += '\n'
        out += self._latex_code_body(indent=indent)
        return out

    @abc.abstractmethod
    def _latex_code_body(self, indent=''):
        pass

    def as_document(self, path='standalone.tex',
                    config=document.STANDALONE_CONFIG):
        return document.LatexDocument(path, config=config, contents=[self])

    def as_project(self, config=document.STANDALONE_CONFIG, proj_fs=None):
        doc = self.as_document(config=config)
        proj = project.LatexProject(proj_fs=proj_fs)
        proj.add_file(doc)
        return proj

    def render(self, config=document.STANDALONE_CONFIG, **pdf_args):
        proj = self.as_project(config=config)
        return proj.compile_pdf(fname='standalone.tex', **pdf_args)

    def save(self, path=None, base_dir=None, dst_fs=None, tmp_dir=None,
             config=document.STANDALONE_CONFIG):
        if (path is not None) + (base_dir is not None) != 1:
            raise ValueError('Specify either path or base_dir')
        if path is not None:
            base_dir = fs.path.dirname(path)
            fname = fs.path.basename(path)
        else:
            fname = 'standalone.tex'
        proj = self.as_project(config=config)
        return proj.save_pdf(fname=fname, base_dir=base_dir, dst_fs=dst_fs,
                             tmp_dir=tmp_dir)


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
