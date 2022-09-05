import os
import re

from setuptools import find_packages, setup
from setuptools.command.install import install

SUPPORTED_VERSIONS = ['3.6', '3.7', '3.8', '3.9']
SUPPORTED_VERSIONS_CLASSIFIERS = ['Programming Language :: Python :: {version}'.format(
    version=version) for version in SUPPORTED_VERSIONS]
CLASSIFIERS = [
    *SUPPORTED_VERSIONS_CLASSIFIERS,
    'Environment :: Console',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
]
with open('README.rst', encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()
HERE = os.path.abspath(os.path.dirname(__file__))


def find_version(*file_paths):
    """Read the version number from a source file.
    Why read it, and not import?
    see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
    """
    with open(os.path.join(HERE, *file_paths), 'r') as f:
        version_file = f.read()

    # The version line must have the form __version__ = 'ver'
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


setup(
    name='secedgar',
    version=find_version('secedgar', '__init__.py'),
    packages=find_packages(exclude=['docs', 'tests*']),
    package_dir={'secedgar': 'secedgar'},
    url='https://github.com/sec-edgar/sec-edgar',
    download_url='https://github.com/sec-edgar/sec-edgar/releases',
    license='Apache License (2.0)',
    author='Rahul Ranjan',
    author_email='rahul.rrixe@gmail.com',
    maintainer='Jack Moody',
    maintainer_email='jacklaytonmoody@gmail.com',
    description="""SEC-Edgar implements a basic crawler for downloading
                 filings from the SEC Edgar database. It is most useful
                 for automatically collecting public filings from the SEC.""",  # noqa: W291
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    entry_points={
        'console_scripts': [
            'secedgar=secedgar.cli:cli'
        ]
    },
    cmdclass={
        'install': install,
    },
    # List run-time dependencies here.
    # These will be installed by pip when your
    # project is installed.
    install_requires=parse_requirements('requirements.txt'),
    keywords=['SEC', 'EDGAR', 'crawler', 'filings'],
    tests_require=parse_requirements('requirements.txt', 'requirements-dev.txt'),
    extras_require={
        'cli': [*parse_requirements('requirements.txt'), "Click"],
        # typing_extensions drops 3.6 support in 4.2.0, but this
        # can sometimes mess up during install
        ':python_version == "3.6"': [
            "typing_extensions<4.2.0"
        ]
    },
    classifiers=CLASSIFIERS,
    # If there are data files included in your packages that need to be
    # installed, specify them here. If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'secedgar': ['requirements.txt',
                     'requirements-dev.txt',
                     'README.rst',
                     'LICENSE'],
    }
)
