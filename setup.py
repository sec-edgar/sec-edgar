# -*- coding:utf-8 -*-
import os
import sys

from setuptools import setup, find_packages
from setuptools import Command
from setuptools.command.install import install
from subprocess import call
from glob import glob
from os.path import splitext, basename, join as pjoin

SUPPORTED_VERSIONS = ['2.5', '2.6', '2.7', 'PyPy', ]

if sys.version_info <= (2, 4):
    version = '.'.join([str(x) for x in sys.version_info[:3]])
    print('Version ' + version + ' is not supported. Supported versions are ' +
          ', '.join(SUPPORTED_VERSIONS))
    sys.exit(1)

setup(
    name='SECEdgar',
    version='0.1.1',
    packages=find_packages(),
    package_dir={'SECEdgar': 'SECEdgar'},
    url='https://github.com/rahulrrixe/SEC-Edgar',
    license='Apache License (2.0)',
    author='Rahul Ranjan',
    author_email='rahul.rrixe@gmail.com',
    description='SEC-Edgar implements a basic Sphinx crwaler for downloading the   \
                 filings. It provides an interface to extract the filing from the SEC.gov site \
                 You might find it most useful for tasks involving automated  \
                 data collection of filings from SEC.gov',
    entry_points='''
            [console_scripts]
            ''',
    cmdclass={
        'install': install,
    },
    install_requires=['requests', 'beautifulsoup4', 'configparser',],
    keywords=['SEC', 'Edgar', 'Crawler', 'filings'],
    tests_require=['unittest2'],
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: PyPy']
)