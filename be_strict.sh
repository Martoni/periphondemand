#!/bin/sh

find periphondemand/ -name "*.py" | xargs pep8

pylint --rcfile=pylint.cfg periphondemand 
