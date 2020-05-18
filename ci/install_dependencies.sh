#!/bin/bash
#
# Sets up dependencies
#
# Usage:
#     $ ./ci/install_dependencies.sh      # runs python setup.py install
#     $ ./ci/install_dependencies.sh dev  # set up dev dependencies as well
python setup.py install

if [[ $(uname) == "Linux" ]]; then
    # Install lxml dependencies
    sudo apt-get update && sudo apt-get install python-dev libxml2-dev libxslt-dev libz-dev
fi

if [[ $1 -eq "dev" ]]; then
    pip install -r requirements-dev.txt
fi
