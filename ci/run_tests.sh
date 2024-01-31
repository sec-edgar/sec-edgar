#!/bin/bash
#
# Runs pytest tests for project
#
# Note that to run all tests with coverage, the order must be cover all, not all cover.
#
# Usage:
#     $ ./ci/run_tests.sh       # Runs all non-smoke tests
#     $ ./ci/run_tests.sh cover # Runs all non-smoke tests with coverage
#     $ ./ci/run_tests.sh all   # Runs all tests (including smoke tests)
#     $ ./ci/run_tests.sh cover all # Runs all tests with coverage (including smoke tests)
echo "Running tests"

if [[ -z "$1" ]]; then
    echo "Running non-smoke without cover"
    pytest secedgar/tests -m "not smoke"  # run non-smoke tests
elif [[ "$1" = "all" ]]; then
    echo "Running all without cover"
    pytest secedgar/tests  # run all tests
elif [[ "$1" = "cover" ]]; then
    if [[ "$2" = "all" ]]; then
        # run all tests (including smoke tests), omit test code from coverage
        echo "Running all with cover"
        coverage run --source secedgar --omit=*/tests* -m pytest
    else
        # run non-smoke tests, omit test code from coverage
        echo "Running non-smoke with cover"
        coverage run --source secedgar --omit=*/tests* -m pytest -m "not smoke"
    fi
    # output coverage results to xml file
    coverage xml -o cov.xml
    # Show missing lines
    coverage report -m
else
    echo "Arguments given not recognized."
    exit 1
fi