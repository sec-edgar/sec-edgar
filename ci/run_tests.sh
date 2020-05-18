#!/bin/bash
#
# Runs pytest tests for project
#
# Usage:
#     $ ./ci/run_tests.sh       # Runs all tests
#     $ ./ci/run_tests.sh cover # Runs all tests with coverage
echo "Running tests"

if [[ -z "$1" ]]; then
    pytest secedgar/tests
elif [[ "$1" -eq "cover" ]]; then
    # run tests, omit tests from coverage
    coverage run --source secedgar --omit=*/tests* -m pytest
    # output coverage results to xml file
    coverage xml -o cov.xml
    # Show missing lines
    coverage report -m
else
    echo "Arguments given not recognized."
    exit 1
fi