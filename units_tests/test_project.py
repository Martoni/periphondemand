#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  17/07/2014
# ----------------------------------------------------------------------------
# Copyright (2014)  Armadeus Systems
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
""" class test_project
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
from periphondemand.bin.core import project

class test_project(unittest.TestCase):
    """ unit tests bin.core.project.py
    """

    def test_initproject(self):
        """ Just instanciate project """
        projectname = "UnitTest"
        os.system("rm -rf " + projectname)
        aproject = project.Project(projectname)
        os.system("rm -rf " + projectname)

    def test_vhdl_version(self):
        """ test vhdl version property """
        projectname = "UnitTest"
        os.system("rm -rf " + projectname)
        aproject = project.Project(projectname)
        self.assertEqual(aproject.vhdl_version, "vhdl87")
        aproject.vhdl_version = "vhdl93"
        self.assertEqual(aproject.vhdl_version, "vhdl93")
        with self.assertRaises(PodError):
            aproject.vhdl_version = "puet"
        os.system("rm -rf " + projectname)

    def test_availables_platforms(self):
        projectname = "UnitTest"
        os.system("rm -rf " + projectname)
        aproject = project.Project(projectname)
        self.assertTrue("apf27" in aproject.availables_plat())
        os.system("rm -rf " + projectname)



if __name__ == "__main__":
    print("test_project class test\n")
    unittest.main(
            testRunner=xmlrunner.XMLTestRunner(
                output='test-reports'))
