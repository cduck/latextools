from .file import LatexFileAbc


class DocumentConfig:
    def __init__(self, doc_type='article', options=(), packages=(),
                 commands=()):
        self.doc_type = doc_type
        self.options = list(options)
        self.packages = list(packages)
        self.commands = list(commands)


class LatexDocument(LatexFileAbc):
    def __init__(self, path, config=DocumentConfig(), contents=()):
        super().__init__(path)
        self.config = config
        self.contents = list(contents)

    def sorted_packages(self):
        packages = set(p for content in self.contents
                         for p in content.required_packages())
        packages.update(self.config.packages)
        return sorted(packages)

    def sorted_commands(self):
        commands = set(c for content in self.contents
                         for c in content.required_commands())
        commands.update(self.config.commands)
        return sorted(commands)

    def _gen_blocks(self):
        options = self.config.options
        options_str = '' if not options else f'[{",".join(options)}]'
        yield f'\documentclass{options_str}{{{self.config.doc_type}}}'

        packages = self.sorted_packages()
        yield '\n'.join(filter(bool, (p.latex_code_import()
                                      for p in packages)))

        yield '\n'.join(filter(bool, (p.latex_code_setup()
                                      for p in self.sorted_commands())))

        yield '\n'.join(filter(bool, (p.latex_code_setup()
                                      for p in packages)))

        yield r'\begin{document}'

        for content in self.contents:
            yield content.latex_code_body(indent='')

        yield r'\end{document}'

    def get_content(self):
        out = '\n\n'.join(filter(bool, map(str.rstrip, self._gen_blocks())))
        out += '\n'
        return out
