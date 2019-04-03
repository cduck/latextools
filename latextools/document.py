from .file import LatexFileAbc
from . import project


class DocumentConfig:
    def __init__(self, doc_type='article', options=(), packages=(),
                 commands=()):
        self.doc_type = doc_type
        self.options = list(options)
        self.packages = list(packages)
        self.commands = list(commands)

STANDALONE_CONFIG = DocumentConfig('standalone')


class LatexDocument(LatexFileAbc):
    def __init__(self, path, config=DocumentConfig(), contents=()):
        super().__init__(path)
        self.config = config
        self.contents = list(contents)

    def sorted_packages(self):
        packages = set(p for content in self.contents
                         for p in content.required_packages())
        packages.update(self.config.packages)
        packages.update(p for c in self.config.commands
                          for p in c.required_packages())
        return sorted(packages)

    def sorted_commands(self):
        commands = set(c for content in self.contents
                         for c in content.required_commands())
        commands.update(self.config.commands)
        commands.update(c for p in self.config.packages
                          for c in p.required_packages())
        return sorted(commands)

    def _gen_preamble_blocks(self):
        packages = self.sorted_packages()
        yield '\n'.join(filter(bool, (p.latex_code_import()
                                      for p in packages)))

        yield from filter(bool, (p.latex_code_setup()
                                 for p in self.sorted_commands()))

        yield from filter(bool, (p.latex_code_setup()
                                 for p in packages))

    def _gen_blocks(self):
        options = self.config.options
        options_str = '' if not options else f'[{",".join(options)}]'
        yield f'\documentclass{options_str}{{{self.config.doc_type}}}'

        yield from self._gen_preamble_blocks()

        yield r'\begin{document}'

        for content in self.contents:
            yield content.latex_code_body(indent='')

        yield r'\end{document}'

    def get_preamble(self):
        out = '\n\n'.join(filter(bool, map(str.rstrip,
                                           self._gen_preamble_blocks())))
        return out

    def get_content(self):
        out = '\n\n'.join(filter(bool, map(str.rstrip, self._gen_blocks())))
        out += '\n'
        return out

    def get_required_files(self):
        for content in self.contents:
            yield from content.get_required_files()

    def as_project(self, proj_fs=None):
        proj = project.LatexProject(proj_fs=proj_fs)
        proj.add_file(self)
        return proj

    def render(self, **pdf_args):
        proj = self.as_project()
        return proj.compile_pdf(fname=self.path, **pdf_args)

    def save_pdf(self, base_dir=None, dst_fs=None, tmp_dir=None):
        proj = self.as_project()
        return proj.save_pdf(fname=self.path, base_dir=base_dir, dst_fs=dst_fs,
                             tmp_dir=tmp_dir)
