import functools

from . import content


@functools.total_ordering
class LatexCommand:
    def __init__(self, name, setup_content, sort_priority=0,
                 packages=(), commands=()):
        self.name = name
        if isinstance(setup_content, str):
            setup_content = content.BasicContent(setup_content)
        self.setup_content = setup_content
        self.sort_priority = sort_priority
        self.packages = list(packages)
        self.commands = list(commands)

    def latex_code_setup(self):
        if self.setup_content is None:
            return None
        return (f'% Command: {self.name}\n'
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
            next(iter(self.required_commands()))
        except StopIteration:
            return 0
        return 1+max(map(LatexCommand.require_depth, self.required_commands()))

    def _key(self):
        if self.setup_content is None:
            content = ''
        else:
            content = self.setup_content.latex_code_body()
        return (-self.sort_priority, self.name, content)

    def _sort_key(self):
        if self.setup_content is None:
            content = ''
        else:
            content = self.setup_content.latex_code_body()
        return (-self.sort_priority, self.require_depth(), self.name, content)

    def __lt__(self, other):
        if not isinstance(other, LatexCommand):
            return NotImplemented
        else:
            return self._sort_key() < other._sort_key()

    def __eq__(self, other):
        if not isinstance(other, LatexCommand):
            return NotImplemented
        else:
            return self._key() == other._key()

    def __hash__(self):
        return hash((LatexCommand, self._key()))

    def can_coexist(self, other):
        return self.name != other.name or not self.name

    def can_merge(self, other):
        return False

    def merge_packages(self, other):
        if not self.can_merge(other):
            raise ValueError(
                    f'Cannot merge commands: {self.name}, {other.name}')


class CommandBundle(LatexCommand):
    def __init__(self, *commands, packages=()):
        super().__init__(None, None, packages=packages, commands=commands)
