import abc

from . import str_util


class FileAbc(metaclass=abc.ABCMeta):
    def __init__(self, path):
        '''
        The base class for files used in a LatexProject.

        Args:
            path: The path within a project where this file expects to be
                placed.
        '''
        self.path = path

    @abc.abstractmethod
    def is_text(self):
        pass

    def write_content(self, f):
        '''
        Returns the text contents of this file.

        Optionally override this in a subclass.

        Args:
            f: A file open for writing.  It should be in byte mode if is_text()
                is false.
        '''
        f.write(self.get_content())

    @abc.abstractmethod
    def get_content(self):
        '''
        Returns the text or byte contents of this file.

        Override this in a subclass.
        '''

    def get_required_files(self):
        '''
        Returns a list of files that this file depends on.

        Optionally override this in a subclass.
        '''
        return ()


class BinaryFile(FileAbc):
    def __init__(self, path, data=None, fname=None):
        if (fname is not None) + (data is not None) != 1:
            raise TypeError('Specify either fname or data.')
        super().__init__(path)
        if data is None:
            with open(fname, 'rb') as f:
                data = f.read()
        self.data = data

    def is_text(self):
        return False

    def get_content(self):
        return self.data


class PlainTextFile(FileAbc):
    def __init__(self, path, text=None, fname=None):
        if (fname is not None) + (text is not None) != 1:
            raise TypeError('Specify either fname or text.')
        super().__init__(path)
        if text is None:
            with open(fname, 'r') as f:
                text = f.read()
        self.text = text

    def is_text(self):
        return True

    def get_content(self):
        return self.text


class LatexFileAbc(FileAbc, metaclass=abc.ABCMeta):
    def write_content(self, f):
        f.write('% This file was automatically generated by python latextools.'
                '\n'
                '% https://github.com/cduck/latextools'
                '\n%\n')
        f.write(self.get_content())

    def is_text(self):
        return True


class InputFile(LatexFileAbc):
    def __init__(self, path, content):
        super().__init__(path)
        self.content = content

    def get_content(self):
        out = str_util.prefix_lines('% ',
                                    self.content.as_document().get_preamble())
        out += '\n%\n'
        out += self.content.latex_code_body() + '\n'
        return out

    def get_required_files(self):
        return self.content.get_required_files()
