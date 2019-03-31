import functools

from . import content


@functools.total_ordering
class LatexPackage:
    def __init__(self, name, options=(), setup_content=None, sort_priority=0,
                 packages=(), commands=()):
        self.name = name
        self.options = tuple(options)
        if isinstance(setup_content, str):
            setup_content = content.BasicContent(setup_content)
        self.setup_content = setup_content
        self.sort_priority = sort_priority
        self.packages = list(packages)
        self.commands = list(commands)

    def latex_code_import(self):
        options_str = '' if not self.options else f'[{",".join(self.options)}]'
        out = rf'\usepackage{options_str}{{{self.name}}}'
        return out

    def latex_code_setup(self):
        if self.setup_content is None:
            return None
        return (f'% Setup package: {self.name}\n'
                + self.setup_content.latex_code_body())

    def required_packages(self):
        yield from self.packages
        if self.setup_content is not None:
            yield from self.setup_content.required_packages()

    def required_commands(self):
        yield from self.commands
        if self.setup_content is not None:
            yield from self.setup_content.required_commands()

    def require_depth(self):
        try:
            next(iter(self.required_packages()))
        except StopIteration:
            return 0
        return 1+max(map(LatexPackage.require_depth, self.required_packages()))

    def _key(self):
        if self.setup_content is None:
            content = ''
        else:
            content = self.setup_content.latex_code_body()
        return (-self.sort_priority, self.name, self.options, content)

    def _sort_key(self):
        if self.setup_content is None:
            content = ''
        else:
            content = self.setup_content.latex_code_body()
        return (-self.sort_priority, self.require_depth(), self.name,
                self.options, content)

    def __lt__(self, other):
        if not isinstance(other, LatexPackage):
            return NotImplemented
        else:
            return self._sort_key() < other._sort_key()

    def __eq__(self, other):
        if not isinstance(other, LatexPackage):
            return NotImplemented
        else:
            return self._key() == other._key()

    def __hash__(self):
        return hash((LatexPackage, self._key()))

    def can_coexist(self, other):
        return self.name != other.name

    def can_merge(self, other):
        return False

    def merge_packages(self, other):
        if not self.can_merge(other):
            raise ValueError(
                    f'Cannot merge packages: {self.name}, {other.name}')
