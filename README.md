POD: PeripheralOnDemand
=======================

POD is a toolbox of Open Source programs simplifying the integration of Virtual
Peripherals (also called components) in FPGAs. A Virtual Peripheral is defined
as a [FPGA IP](http://en.wikipedia.org/wiki/IP_core) providing a bus interface.

POD is designed to be use by embedded system developers. Beginners with a small
knowledge in digital design (FPGA design) will be able to easily integrate and
configure virtual peripherals on their platform (an electronic board equiped
with a FPGA).

POD was initially designed for platforms with one main processor connected to
one FPGA, other architectures can be although supported. 

Prerequisites
=============

Mandatory
---------

* *Python 3*: POD uses python 3.4+.

Optional
--------

* *ghdl, gtkwave* : POD can generate VHDL testbench ready for ghdl simulator. As it's standard VHDL, another simulator should work.
* *ISE Webpack* : to generate synthesis project for Xilinx.
* *Quartus* : to generate synthesis project for Altera.
* *ARMadeus SDK* : to generate driver project for the Armadeus boards.
* *python-coverage* : for unittest and functionnal test.

From GIT
========

**For developpers**

Checkout the source code of periphondemand with the following command (git is needed):

``$ git clone https://github.com/Martoni/fpgarchitect.git periphondemand``

Then checkout the standard library:

``$ git clone https://github.com/Martoni/pod_lib.git libraries``

**Install it**

To install it on your computer, just do (has super user):

``$ python setup.py install``

**Make a distribution archive**

Make python POD distribution with command:

``$ python setup.py sdist``

The POD package can be found in directory dist/


From Package
============

Decompress the package PeriphOnDemand-X.X.tar.gz in install directory:

``$ tar -zxvf PeriphOnDemand-X.X.tar.gz``

Walk through periphondemand/ directory:

``$ cd periphondemand``

Then install POD with root privilege:

``$ python setup.py install``

Enjoy
=====

To launch periphondemand just type «pod»:

``$ pod``

Tests
=====

Python mock package is required to run units-tests, in debian do :

``$ sudo apt-get install python-mock``

To run test do :

``$ ./runtests.sh``

Documentation
=============

To generate documentation python-sphinx module is required.
In debian do :

``$ sudo apt-get install python-sphinx``

Then go to doc/ directory and type :

``$ make latexpdf``

To generate pdf document or :

``$ make html``

To generate static html website.
