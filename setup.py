# -*- coding:utf-8 -*-
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install

SUPPORTED_VERSIONS = ['2.7', '3.5', '3.6', 'PyPy', ]

if sys.version_info <= (2, 4):
    version = '.'.join([str(x) for x in sys.version_info[:3]])
    suppored_versions = ', '.join(SUPPORTED_VERSIONS)
    print('Version {version} is not supported. Supported versions are {supported_versions}'
          .format(version=version, supported_versions=SUPPORTED_VERSIONS)
          )
    sys.exit(1)


def parse_requirements(filename):

    with open(filename) as f:
        required = f.read().splitlines()
        return required


setup(
    name='SECEdgar',
    version='0.1.3',
    packages=find_packages(),
    package_dir={'SECEdgar': 'SECEdgar'},
    url='https://github.com/rahulrrixe/SEC-Edgar',
    license='Apache License (2.0)',
    author='Rahul Ranjan',
    author_email='rahul.rrixe@gmail.com',
    description="""SEC-Edgar implements a basic Sphinx crwaler for downloading the 
                 filings. It provides an interface to extract the filing from 
                 the SEC.gov site. You might find it most useful for tasks 
                 involving automated data collection of filings from SEC.gov""",
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
        'Programming Language :: Python :: Implementation :: PyPy']
)
