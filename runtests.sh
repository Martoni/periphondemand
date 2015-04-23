#!/bin/sh
rm -rf htmlcov
rm -rf .coverage
rm -rf coverage.xml
ln -s periphondemand src
export PYTHONPATH=./:$PYTHONPATH
python-coverage run -a --source periphondemand --branch units_tests/test_project.py
python-coverage run -a --source periphondemand --branch units_tests/test_port.py
python-coverage run -a --source periphondemand --branch functionals_tests/test_launcher.py
python -m coverage xml
python -m coverage html
