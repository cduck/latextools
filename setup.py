from setuptools import setup, find_packages
import logging
logger = logging.getLogger(__name__)

version = '0.3.0'

try:
    with open('README.md', 'r') as f:
        long_desc = f.read()
except:
    logger.warning('Could not open README.md.  long_description will be set to None.')
    long_desc = None

setup(
    name = 'latextools',
    packages = find_packages(),
    version = version,
    description = 'A library of tools for programmatically generating LaTeX code.',
    long_description = long_desc,
    long_description_content_type = 'text/markdown',
    author = 'Casey Duckering',
    #author_email = '',
    url = 'https://github.com/cduck/latextools',
    download_url = 'https://github.com/cduck/latextools/archive/{}.tar.gz'.format(version),
    keywords = ['LaTeX'],
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Framework :: IPython',
        'Framework :: Jupyter',
    ],
    install_requires = [
        'fs',
    ],
    extras_require = {
        'dev': [
            'twine',
        ]
    },
)

