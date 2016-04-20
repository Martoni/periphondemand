#!/bin/sh
rm -rf htmlcov
rm -rf .coverage
rm -rf coverage.xml
ln -s src periphondemand
python3-coverage run -a --source periphondemand --branch units_tests/test_project.py
python3-coverage run -a --source periphondemand --branch units_tests/test_port.py
python3-coverage run -a --source periphondemand --branch functionals_tests/test_launcher.py
python3 -m coverage xml
python3 -m coverage html
