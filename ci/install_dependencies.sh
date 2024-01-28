#!/bin/bash
#
# Sets up dependencies
#
# Usage:
#     $ ./ci/install_dependencies.sh      # runs python setup.py install
#     $ ./ci/install_dependencies.sh dev  # set up dev dependencies as well
#     $ ./ci/install_dependencies.sh docs # set up dependencies for building docs
#     $ ./ci/install_dependencies.sh pypi # set up dependencies for deploying to PyPi
if [[ $(uname) == "Linux" ]]; then
    # Install lxml dependencies
    sudo apt-get update && sudo apt-get install python-dev libxml2-dev libxslt-dev libz-dev python3-setuptools
fi

# Both dev and docs dependencies require dev dependencies
if [[ "$1" -eq "dev" || "$1" -eq "docs" ]]; then
    python setup.py install
    pip install -r requirements-dev.txt
fi

if [[ "$1" -eq "docs" ]]; then
    pip install ipython sphinx_rtd_theme sphinx sphinx-autobuild sphinx-click
fi

if [[ "$1" -eq "pypi" ]]; then
    python -m pip install --upgrade pip
    pip install setuptools wheel twine
fi
