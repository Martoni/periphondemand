#! /usr/bin/python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Simulation.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  16/07/2008
# ----------------------------------------------------------------------------
#  Copyright (2008)  Armadeus Systems
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ----------------------------------------------------------------------------
""" Simulation toolchain """

from periphondemand.bin.define import XMLEXT
from periphondemand.bin.define import SIMULATIONPATH
from periphondemand.bin.define import TOOLCHAINPATH

from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils import wrappersystem as sy
from periphondemand.bin.utils.display import Display
from periphondemand.bin.utils.poderror import PodError

SETTINGS = Settings()
DISPLAY = Display()


class Simulation(WrapperXml):
    """ Manage simulation
    """

    def __init__(self, parent):
        self.parent = parent
        filepath = self.parent.projectpath + "/" +\
            SIMULATIONPATH + "/simulation" + XMLEXT
        if not sy.file_exist(filepath):
            raise PodError("No simulation project found", 3)
        WrapperXml.__init__(self, file=filepath)

    @classmethod
    def generate_project(cls):
        """TODO: Generate the project """
        DISPLAY.msg("TODO")

    @property
    def lib_name(self):
        """ Get library name """
        return self.get_node("library").get_attr_value("name")

    @property
    def lang_name(self):
        """ Get langage name """
        return self.get_node("language").get_attr_value("name")

    def generate_template(self):
        """ Generate simulation template """
        import sys
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SIMULATIONPATH + "/" + self.name)
        try:
            plugin = __import__(self.name)
        except ImportError, error:
            sys.path.remove(SETTINGS.path + TOOLCHAINPATH +
                            SIMULATIONPATH + "/" + self.name)
            raise PodError(str(error), 0)
        sys.path.remove(SETTINGS.path + TOOLCHAINPATH +
                        SIMULATIONPATH + "/" + self.name)
        return plugin.generate_template()

    def generate_makefile(self):
        """ Generate simulation makefile """
        import sys
        sys.path.append(SETTINGS.path + TOOLCHAINPATH +
                        SIMULATIONPATH + "/" + self.name)
        try:
            plugin = __import__(self.name)
        except ImportError, error:
            sys.path.remove(SETTINGS.path + TOOLCHAINPATH +
                            SIMULATIONPATH + "/" + self.name)
            raise PodError(str(error), 0)
        sys.path.remove(SETTINGS.path + TOOLCHAINPATH +
                        SIMULATIONPATH + "/" + self.name)
        return plugin.generate_makefile()

    def save(self):
        """ save project """
        self.save_xml(self.parent.projectpath +
                      "/simulation/simulation" + XMLEXT)
