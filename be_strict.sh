#!/bin/sh

find src/ -name "*.py" | xargs pep8

pylint --rcfile=pylint.cfg src
