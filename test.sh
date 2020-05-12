#!/bin/sh
# run tests, omit tests
coverage run --source secedgar --omit=*/tests* -m pytest
# output coverage results to xml file
coverage xml -o cov.xml
# Show missing lines
coverage report -m