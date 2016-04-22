#! /usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Bus.py
# Purpose:
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
# Created:  30/04/2008
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
""" Manage busses """

from periphondemand.bin.define import BUSPATH

from periphondemand.bin.utils.wrapperxml import WrapperXml
from periphondemand.bin.utils.settings import Settings
from periphondemand.bin.utils.poderror import PodError

SETTINGS = Settings()


class Bus(WrapperXml):
    """ Class for bus type
        attributes:
            settings --
    """

    def __init__(self, parent, name):
        self.parent = parent
        WrapperXml.__init__(self, file=(SETTINGS.path + BUSPATH + "/" +
                            name + "/" + name + ".xml"))

    @property
    def data_size(self):
        """ Get size of data"""
        size = self.get_attr_value("datasize")
        if size is None:
            raise PodError("No datasize attribute in bus " + self.name, 0)
        else:
            return size

    def sig_name(self, classname, typename):
        """ return the signal name for a given type
        """
        for classnode in self.get_nodes("class"):
            if classnode.get_attr_value("type") == classname:
                for signal in classnode.get_nodes("type"):
                    if signal.get_attr_value("type") == typename:
                        return signal.get_attr_value("name")
        return None

    def generate_intercon(self, intercon):
        """ generate intercon
        """
        masterinterface = self.parent
        import sys
        # load module path
        sys.path.append(SETTINGS.path + BUSPATH + "/" + self.name)
        plugin = __import__(self.name)
        sys.path.remove(SETTINGS.path + BUSPATH + "/" + self.name)

        plugin.generate_intercon(masterinterface, intercon)
