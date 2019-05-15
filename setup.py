# -*- coding:utf-8 -*-
import sys
import os
import re
import codecs
from setuptools import setup, find_packages
from setuptools.command.install import install

SUPPORTED_VERSIONS = ['2.7', '3.5', '3.6', '3.7', ]
here = os.path.abspath(os.path.dirname(__file__))


def find_version(*file_paths):
    """Read the version number from a source file.
    Why read it, and not import?
    see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
    """
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def parse_requirements(filename):

    with open(filename) as f:
        required = f.read().splitlines()
        return required


# Get the long description from the relevant file
with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='SECEdgar',
    version=find_version('SECEdgar', '__init__.py'),
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'SECEdgar': 'SECEdgar'},
    url='https://github.com/rahulrrixe/SEC-Edgar',
    license='Apache License (2.0)',
    author='Rahul Ranjan',
    author_email='rahul.rrixe@gmail.com',
    description="""SEC-Edgar implements a basic crawler for downloading 
                 filings from the SEC Edgar database. It is most useful 
                 for automatically collecting public filings from the SEC.""",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    entry_points='''
            [console_scripts]
            ''',
    cmdclass={
        'install': install,
    },
    install_requires=parse_requirements('requirements.txt'),
    keywords=['SEC', 'Edgar', 'Crawler', 'filings'],
    tests_require=parse_requirements('requirements.txt'),
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    package_data={
        'SECEdgar': [],
    }
)
