#!/bin/bash -e
#
# Runs flake8 linting
#
# This script is intended for CI and developers to check that
# linting standards are upheld.
#
# Usage:
#     $ ./ci/lint.sh    # flake8 check

echo "Using flake8 version $(flake8 --version)"
flake8 secedgar --count --show-source --statistics