import abc

import fs

from . import str_util, document, project, file


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
        out += self._latex_code_body(indent=indent).rstrip()
        return out

    @abc.abstractmethod
    def _latex_code_body(self, indent=''):
        pass

    def as_document(self, path='standalone.tex',
                    config=document.STANDALONE_CONFIG):
        return document.LatexDocument(path, config=config, contents=[self])

    def as_project(self, path='standalone.tex',
                   config=document.STANDALONE_CONFIG, proj_fs=None):
        return self.as_document(path=path, config=config
                               ).as_project(proj_fs=proj_fs)

    def render(self, config=document.STANDALONE_CONFIG, **pdf_args):
        fname = 'standalone.tex'
        proj = self.as_project(path=fname, config=config)
        return proj.compile_pdf(fname=fname, **pdf_args)

    def save_pdf(self, path=None, base_dir=None, dst_fs=None, tmp_dir=None,
                 config=document.STANDALONE_CONFIG):
        if (path is not None) + (base_dir is not None) != 1:
            raise ValueError('Specify either path or base_dir')
        if path is not None:
            base_dir = fs.path.dirname(path)
            fname = fs.path.basename(path)
            if fname.lower().endswith('.pdf'):
                fname = fname[:-4] + '.tex'
        else:
            fname = 'standalone.tex'
        proj = self.as_project(path=fname, config=config)
        return proj.save_pdf(fname=fname, base_dir=base_dir, dst_fs=dst_fs,
                             tmp_dir=tmp_dir)

    def separate_file(self, path):
        return InputContent(path, self, comment=self.comment)


class BasicContent(LatexContentAbc):
    def __init__(self, latex_code, packages=(), commands=(), comment=None):
        super().__init__(packages, commands, comment=comment)
        self.latex_code = latex_code

    def _latex_code_body(self, indent=''):
        return '\n'.join(f'{indent}{s}'.rstrip()
                         for s in self.latex_code.strip().split('\n'))


class MultiContent(LatexContentAbc):
    def __init__(self, *contents, comment=None, between='\n\n', pre=None,
                 post=None):
        super().__init__((), (), comment=comment)
        self.contents = list(contents)
        self.between = between
        self.pre = pre
        self.post = post

    def list_sub_content(self):
        return self.contents

    def _latex_code_body(self, indent=''):
        out = ''
        if self.pre is not None:
            out += self.pre
            out += '\n'
        out += self.between.join(filter(bool, (c.latex_code_body(indent=indent)
                                               for c in self.contents)))
        if self.post is not None:
            out += '\n'
            out += self.post
        return out


class InputContent(LatexContentAbc):
    def __init__(self, path, content, comment=None):
        super().__init__((), (), comment=comment)
        self.path = path
        self.file = file.InputFile(path, content)

    def list_sub_content(self):
        return [self.file.content]

    def _latex_code_body(self, indent=''):
        return indent + fr'\input{{{self.path}}}%'

    def get_required_files(self):
        return [self.file]

    def save_tex(self, base_dir=None, dst_fs=None):
        doc = self.as_document(config=document.DocumentConfig())
        proj = project.LatexProject()
        for f in doc.get_required_files():
            proj.add_file(f)
        proj.write_src(base_dir=base_dir, dst_fs=dst_fs)
