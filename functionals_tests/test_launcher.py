#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  17/07/2014
# ----------------------------------------------------------------------------
#  Copyright (2014)  Armadeus Systems
# ----------------------------------------------------------------------------
""" class test_launcher
"""

import sys
sys.path.append("./")
import xmlrunner
import unittest
import os

from periphondemand.bin import pod 

class test_launcher(unittest.TestCase):
    """
    """

    def test_apf27_i2cledbuttonextint(self):
        """ testing apf27_uarts_gpios script"""
        os.system("rm -rf  i2cledbuttonextint")
        with self.assertRaises(SystemExit):
            pod.main(['pod',
                      '-s',
                      'functionals_tests/apf27_i2cledbuttonextint.pod'])
        self.assertTrue(os.path.isfile("i2cledbuttonextint/objs/top_i2cledbuttonextint.bit"))
        os.system("rm -rf  i2cledbuttonextint")

    def test_apf27_uarts_gpios(self):
        """ testing apf27_uarts_gpios script"""
        os.system("rm -rf  apf27uartgpio")
        with self.assertRaises(SystemExit):
            pod.main(['pod', '-s', 'functionals_tests/apf27_uarts_gpios.pod'])
        self.assertTrue(os.path.isfile("apf27uartgpio/objs/top_apf27uartgpio.bit"))
        os.system("rm -rf  apf27uartgpio")


if __name__ == "__main__":
    print "Functionnals tests launcher"
    unittest.main(
            testRunner=xmlrunner.XMLTestRunner(
                output='test-reports'))
