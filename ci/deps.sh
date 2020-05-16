#!/bin/bash
#
# Sets up dependencies
#
# Usage:
#     $ ./ci/deps.sh      # runs python setup.py install
#     $ ./ci/deps.sh dev  # set up only dev dependencies
python setup.py install

if [[ $(uname) == "Linux" ]]; then
    # Install lxml deps
    sudo apt-get update && sudo apt-get install python-dev libxml2-dev libxslt-dev libz-dev
fi

if [[ $1 -eq "dev" ]]; then
    pip install -r requirements-dev.txt
fi
