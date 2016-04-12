#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  17/07/2014
# ----------------------------------------------------------------------------
# Copyright (2014)  Armadeus Systems
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
""" class test_port
"""

import sys
sys.path.append("./")
import xmlrunner
import unittest
import os
from mock import patch, sentinel
from mock import MagicMock
from mock import Mock
from datetime import datetime

from periphondemand.bin.utils.poderror import PodError
from periphondemand.bin.core.port import Port

class test_port(unittest.TestCase):
    """ unit tests bin.core.project.py
    """

    def test_initport(self):
        """ Just instanciate a port """
        aport = Port(None, name="simpleport")

    def test_force(self):
        """ Just instanciate a port """
        aport = Port(None, name="simpleport")
        aport.force = "gnd"
        aport.force = "vcc"
        aport.force = "undef"
        self.assertEqual(aport.force, "undef")
        with self.assertRaises(PodError):
            aport.force = "pouet"

if __name__ == "__main__":
    print("test_project class test\n")
    unittest.main(
            testRunner=xmlrunner.XMLTestRunner(
                output='test-reports'))
