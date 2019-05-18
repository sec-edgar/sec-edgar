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


def parse_requirements(*files):
    required = []
    for file in files:
        with open(file) as f:
            required.append(f.read().splitlines())
    return required


# Get the long description from the relevant file
with codecs.open('README.rst', encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()


setup(
    name='SECEdgar',
    version=find_version('SECEdgar', '__init__.py'),
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'SECEdgar': 'SECEdgar'},
    url='https://github.com/rahulrrixe/SEC-Edgar',
    download_url='https://github.com/rahulrrixe/SEC-Edgar/releases',
    license='Apache License (2.0)',
    author='Rahul Ranjan',
    author_email='rahul.rrixe@gmail.com',
    description="""SEC-Edgar implements a basic crawler for downloading 
                 filings from the SEC Edgar database. It is most useful 
                 for automatically collecting public filings from the SEC.""",
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    entry_points='''
            [console_scripts]
            ''',
    cmdclass={
        'install': install,
    },

    # List run-time dependencies here. These will be installed by pip when your
    # project is installed.
    install_requires=parse_requirements('requirements.txt'),
    keywords=['SEC', 'Edgar', 'Crawler', 'filings'],
    test_suite='pytest',
    setup_requires=['pytest-runner'],
    tests_require=parse_requirements('requirements.txt', 'requirements-dev.txt'),
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
    # If there are data files included in your packages that need to be
    # installed, specify them here. If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'SECEdgar': [],
    }
)
