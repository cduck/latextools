import tempfile
import subprocess

import fs.memoryfs

from .pdf import Pdf
from .file import FileAbc


class LatexError(RuntimeError): pass


class LatexProject:
    def __init__(self, proj_fs=None):
        if proj_fs is None:
            proj_fs = fs.memoryfs.MemoryFS()
        self.proj_fs = proj_fs
        self.file_map = {}

    def add_file(self, path_or_obj, text=None, data=None, file=None,
                 fname=None):
        if isinstance(path_or_obj, FileAbc):
            obj = path_or_obj
            path = obj.path
        else:
            path = path_or_obj
            obj = None
        if ((obj is not None)
                + (text is not None)
                + (data is not None)
                + (file is not None)
                + (fname is not None)) != 1:
            raise TypeError(
                    'Specify exactly one of text, data, file, or fname.')
        if path in self.file_map:
            if obj == self.file_map[path]:
                # obj has already been added
                return
            else:
                raise RuntimeError(f'Two files with the same path: {path}')
        if fname is not None:
            with open(fname, 'rb') as f:
                self.add_file(path, file=f)
        elif file is not None:
            self.file_map[path] = None
            self.proj_fs.makedir(fs.path.dirname(path), recreate=True)
            self.proj_fs.writefile(path, file)
        elif data is not None:
            self.file_map[path] = None
            self.proj_fs.makedir(fs.path.dirname(path), recreate=True)
            self.proj_fs.writebytes(path, data)
        elif text is not None:
            self.file_map[path] = None
            self.proj_fs.makedir(fs.path.dirname(path), recreate=True)
            self.proj_fs.writetext(path, text)
        else:
            self.file_map[path] = obj
            for sub in obj.get_required_files():
                self.add_file(sub)
            self.proj_fs.makedir(fs.path.dirname(path), recreate=True)
            if obj.is_text():
                with self.proj_fs.open(path, 'w') as f:
                    obj.write_content(f)
            else:
                with self.proj_fs.open(path, 'wb') as f:
                    obj.write_content(f)

    @staticmethod
    def _get_fs(base_dir=None, dst_fs=None):
        if (base_dir is not None) + (dst_fs is not None) < 1:
            raise TypeError('Specify at least one argument.')
        if base_dir is None:
            return dst_fs
        elif dst_fs is None:
            return fs.open_fs(base_dir, writeable=True)
        else:
            return dst_fs.opendir(base_dir)

    def write_src(self, base_dir=None, dst_fs=None):
        dst_fs = self._get_fs(base_dir, dst_fs)
        fs.copy.copy_dir(self.proj_fs, '/', dst_fs, '/')

    @staticmethod
    def _get_output_fname(fname, out_extension='pdf'):
        comps = fname.split('.')
        if len(comps) <= 1:
            comps.append(out_extension)
        else:
            comps[-1] = out_extension
        return '.'.join(comps)

    def compile_pdf(self, fname='main.tex', tmp_dir=None,
                    return_path=False, options=None, **pdf_args):
        return self.compile_pdf_batch([fname], tmp_dir=tmp_dir,
                                      return_path=return_path,
                                      options=options,
                                      **pdf_args)[0]

    def compile_pdf_batch(self, fname_list, tmp_dir=None,
                          return_path=False, options=None, **pdf_args):
        if tmp_dir is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                return self.compile_pdf_batch(
                                fname_list, tmp_dir=tmp_dir,
                                return_path=return_path,
                                options=options,
                                **pdf_args)
        tmp_fs = fs.open_fs(tmp_dir, writeable=False)
        self.write_src(tmp_dir)
        out_list = []
        for fname in fname_list:
            fpath = fs.path.join(tmp_dir, fname)
            if options is None:
                self.run_pdflatex(fpath, cwd=tmp_dir)
            else:
                self.run_pdflatex(fpath, cwd=tmp_dir, options=options)
            out_fname = self._get_output_fname(fname, 'pdf')
            data = None
            if tmp_fs.exists(out_fname):
                if not return_path:
                    data = tmp_fs.readbytes(out_fname)
            else:
                out_fname = None
            if return_path:
                out_list.append(out_fname)
            else:
                log_fname = self._get_output_fname(fname, 'log')
                if tmp_fs.exists(log_fname):
                    log = tmp_fs.readtext(log_fname)
                else:
                    log = None
                pdf = Pdf(data=data, log=log, **pdf_args)
                out_list.append(pdf)
        return out_list

    def save_pdf(self, fname='main.tex', base_dir=None, dst_fs=None,
                 tmp_dir=None):
        self.save_pdf_batch([fname], base_dir=base_dir, dst_fs=dst_fs,
                            tmp_dir=tmp_dir)

    def save_pdf_batch(self, fname_list, base_dir=None, dst_fs=None,
                       tmp_dir=None):
        if tmp_dir is None:
            with tempfile.TemporaryDirectory() as tmp_dir:
                return self.save_pdf_batch(
                            fname_list, base_dir=base_dir,
                            dst_fs=dst_fs, tmp_dir=tmp_dir)

        dst_fs = self._get_fs(base_dir, dst_fs)
        base_dir = '/'
        tmp_fs = fs.open_fs(tmp_dir, writeable=False)

        out_fname_list = self.compile_pdf_batch(
                                fname_list, tmp_dir=tmp_dir,
                                return_path=True)
        for _, fname in zip(fname_list, out_fname_list):
            if fname is None:
                continue
            dst_fs.makedir(fs.path.dirname(fname), recreate=True)
            fs.copy.copy_file(tmp_fs, fname, dst_fs, fname)
        for in_fname, fname in zip(fname_list, out_fname_list):
            if fname is None:
                raise LatexError(
                    f'Output file not generated from source file {in_fname}')

    def run_pdflatex(self, fpath, cwd,
                     options=('-halt-on-error', '-file-line-error',
                              '-interaction', 'nonstopmode')):
        try:
            p = subprocess.Popen(['pdflatex', *options, fpath],
                                 cwd=cwd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise LatexError('Latex compiler pdflatex not found.')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            # pdflatex had an error
            msg = ''
            if stdout:
                msg += stdout.decode()
            if stderr:
                msg += stderr.decode()
            raise LatexError(msg)
